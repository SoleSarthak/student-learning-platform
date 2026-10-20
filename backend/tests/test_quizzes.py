from tests.helpers import API, answers, build_course, make_user


def _enroll(client, student, course_id):
    response = client.post(
        f"{API}/enrollments/courses/{course_id}",
        headers=student["headers"],
    )
    assert response.status_code == 201


def _complete(client, student, lesson_id):
    return client.post(
        f"{API}/progress/lessons/{lesson_id}/complete",
        headers=student["headers"],
    )


def _submit(client, student, built, payload):
    return client.post(
        f"{API}/quizzes/{built['quiz_id']}/submit",
        headers=student["headers"],
        json=payload,
    )


def _setup(client, db_session, **kwargs):
    instructor = make_user(client, db_session, "instructor")
    student = make_user(client, db_session, "student")
    built = build_course(client, instructor, **kwargs)

    return instructor, student, built


def test_questions_never_include_the_answer_key(client, db_session):
    _instructor, student, built = _setup(client, db_session)
    _enroll(client, student, built["course_id"])

    response = client.get(
        f"{API}/quizzes/{built['quiz_id']}/questions",
        headers=student["headers"],
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    for question in response.json():
        assert "correct_answer" not in question


def test_questions_and_submit_require_enrollment(client, db_session):
    _instructor, student, built = _setup(client, db_session)

    questions = client.get(
        f"{API}/quizzes/{built['quiz_id']}/questions",
        headers=student["headers"],
    )
    assert questions.status_code == 403

    submit = _submit(client, student, built, answers(built["question_ids"]))
    assert submit.status_code == 403


def test_invalid_answer_letter_is_rejected(client, db_session):
    _instructor, student, built = _setup(client, db_session)
    _enroll(client, student, built["course_id"])

    response = _submit(client, student, built, answers(built["question_ids"], "Z"))

    assert response.status_code == 422


def test_wrong_answers_fail(client, db_session):
    _instructor, student, built = _setup(client, db_session)
    _enroll(client, student, built["course_id"])

    result = _submit(
        client, student, built, answers(built["question_ids"], "B")
    ).json()

    assert result["score"] == 0
    assert result["passed"] is False
    assert result["certificate_issued"] is False


def test_repeating_one_correct_answer_cannot_inflate_the_score(client, db_session):
    # Regression: this used to score 5/2 = 250% and pass.
    _instructor, student, built = _setup(
        client, db_session, questions=2, passing_score=100
    )
    _enroll(client, student, built["course_id"])

    first_question = built["question_ids"][0]
    payload = {
        "answers": [{"question_id": first_question, "answer": "A"}] * 5
    }

    result = _submit(client, student, built, payload).json()

    assert result["score"] == 1
    assert result["total_questions"] == 2
    assert result["percentage"] == 50.0
    assert result["passed"] is False


def test_quiz_without_questions_cannot_be_submitted(client, db_session):
    _instructor, student, built = _setup(client, db_session, questions=0)
    _enroll(client, student, built["course_id"])

    response = _submit(client, student, built, {"answers": []})

    assert response.status_code == 400


def test_certificate_needs_lessons_and_quiz_in_either_order(
    client, db_session, notifications
):
    _instructor, student, built = _setup(client, db_session, lessons=2)
    _enroll(client, student, built["course_id"])

    # 1) Pass the quiz first: no certificate yet, 2 lessons still to do.
    passed = _submit(client, student, built, answers(built["question_ids"])).json()

    assert passed["passed"] is True
    assert passed["certificate_issued"] is False
    assert passed["certificate_number"] is None
    assert passed["lessons_remaining"] == 2

    # 2) Finish lesson 1: still no certificate.
    first = _complete(client, student, built["lesson_ids"][0]).json()
    assert first["certificate_number"] is None

    # 3) Finish the last lesson: certificate is issued automatically.
    last = _complete(client, student, built["lesson_ids"][1]).json()
    assert last["certificate_number"] is not None
    assert last["certificate_number"].startswith("CERT-")

    mine = client.get(f"{API}/certificates", headers=student["headers"]).json()

    assert len(mine) == 1
    assert mine[0]["certificate_number"] == last["certificate_number"]
    assert mine[0]["course_id"] == built["course_id"]
    assert mine[0]["course_title"]

    # The background notification was queued exactly once.
    assert notifications == [(student["email"], last["certificate_number"])]


def test_certificate_when_lessons_are_done_before_the_quiz(client, db_session):
    _instructor, student, built = _setup(client, db_session, lessons=2)
    _enroll(client, student, built["course_id"])

    for lesson_id in built["lesson_ids"]:
        done = _complete(client, student, lesson_id).json()
        assert done["certificate_number"] is None  # quiz not passed yet

    result = _submit(client, student, built, answers(built["question_ids"])).json()

    assert result["passed"] is True
    assert result["certificate_issued"] is True
    assert result["certificate_number"].startswith("CERT-")


def test_retaking_the_quiz_does_not_create_a_second_certificate(
    client, db_session, notifications
):
    _instructor, student, built = _setup(client, db_session, lessons=1)
    _enroll(client, student, built["course_id"])
    _complete(client, student, built["lesson_ids"][0])

    first = _submit(client, student, built, answers(built["question_ids"])).json()
    again = _submit(client, student, built, answers(built["question_ids"])).json()

    assert first["certificate_issued"] is True
    assert again["certificate_issued"] is False
    assert again["certificate_number"] == first["certificate_number"]

    mine = client.get(f"{API}/certificates", headers=student["headers"]).json()

    assert len(mine) == 1
    assert len(notifications) == 1


def test_attempt_history_is_returned_newest_first(client, db_session):
    _instructor, student, built = _setup(client, db_session)
    _enroll(client, student, built["course_id"])

    _submit(client, student, built, answers(built["question_ids"], "B"))
    _submit(client, student, built, answers(built["question_ids"], "A"))

    history = client.get(
        f"{API}/quizzes/{built['quiz_id']}/attempts",
        headers=student["headers"],
    ).json()

    assert len(history) == 2
    assert history[0]["passed"] is True
    assert history[1]["passed"] is False


def test_public_certificate_verification_hides_internal_ids(client, db_session):
    _instructor, student, built = _setup(client, db_session, lessons=1)
    _enroll(client, student, built["course_id"])
    _complete(client, student, built["lesson_ids"][0])

    number = _submit(
        client, student, built, answers(built["question_ids"])
    ).json()["certificate_number"]

    # No login needed.
    response = client.get(f"{API}/certificates/verify/{number}")

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is True
    assert body["certificate_number"] == number
    assert body["student_name"]
    assert body["course_title"]
    assert "student_id" not in body
    assert "course_id" not in body


def test_verifying_an_unknown_certificate_is_404(client):
    assert client.get(f"{API}/certificates/verify/CERT-DOESNOTEXIST").status_code == 404
