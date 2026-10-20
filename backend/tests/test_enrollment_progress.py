from tests.helpers import API, build_course, make_user


def _setup(client, db_session, lessons=2):
    instructor = make_user(client, db_session, "instructor")
    student = make_user(client, db_session, "student")
    built = build_course(client, instructor, lessons=lessons)

    return instructor, student, built


def test_enroll_requires_login(client, db_session):
    _instructor, _student, built = _setup(client, db_session)

    response = client.post(f"{API}/enrollments/courses/{built['course_id']}")

    assert response.status_code == 401


def test_enroll_and_duplicate_enroll(client, db_session):
    _instructor, student, built = _setup(client, db_session)
    url = f"{API}/enrollments/courses/{built['course_id']}"

    first = client.post(url, headers=student["headers"])
    assert first.status_code == 201
    assert first.json()["course_id"] == built["course_id"]

    second = client.post(url, headers=student["headers"])
    assert second.status_code == 409

    mine = client.get(f"{API}/enrollments", headers=student["headers"])
    assert [item["course_id"] for item in mine.json()] == [built["course_id"]]


def test_enroll_in_missing_course_is_404(client, db_session):
    student = make_user(client, db_session, "student")

    response = client.post(
        f"{API}/enrollments/courses/2000000000",
        headers=student["headers"],
    )

    assert response.status_code == 404


def test_lesson_content_requires_login_and_enrollment(client, db_session):
    instructor, student, built = _setup(client, db_session)
    lesson_url = f"{API}/lessons/{built['lesson_ids'][0]}"

    assert client.get(lesson_url).status_code == 401
    assert client.get(lesson_url, headers=student["headers"]).status_code == 403

    client.post(
        f"{API}/enrollments/courses/{built['course_id']}",
        headers=student["headers"],
    )

    enrolled = client.get(lesson_url, headers=student["headers"])
    assert enrolled.status_code == 200
    assert enrolled.json()["course_id"] == built["course_id"]

    # The course owner can always read their own content.
    assert client.get(lesson_url, headers=instructor["headers"]).status_code == 200


def test_lessons_by_module_are_gated_too(client, db_session):
    _instructor, student, built = _setup(client, db_session)
    url = f"{API}/modules/{built['module_id']}/lessons"

    assert client.get(url, headers=student["headers"]).status_code == 403


def test_lesson_video_url_must_be_http(client, db_session):
    instructor, _student, built = _setup(client, db_session)

    response = client.post(
        f"{API}/modules/{built['module_id']}/lessons",
        headers=instructor["headers"],
        json={
            "title": "Bad link",
            "content": "x",
            "order": 99,
            "video_url": "javascript:alert(1)",
        },
    )

    assert response.status_code == 422


def test_cannot_complete_lesson_without_enrolling(client, db_session):
    _instructor, student, built = _setup(client, db_session)

    response = client.post(
        f"{API}/progress/lessons/{built['lesson_ids'][0]}/complete",
        headers=student["headers"],
    )

    assert response.status_code == 403


def test_progress_requires_enrollment(client, db_session):
    _instructor, student, built = _setup(client, db_session)

    response = client.get(
        f"{API}/progress/courses/{built['course_id']}",
        headers=student["headers"],
    )

    assert response.status_code == 403


def test_completing_lessons_updates_progress_and_is_idempotent(client, db_session):
    _instructor, student, built = _setup(client, db_session, lessons=2)

    client.post(
        f"{API}/enrollments/courses/{built['course_id']}",
        headers=student["headers"],
    )

    first_lesson = built["lesson_ids"][0]
    complete_url = f"{API}/progress/lessons/{first_lesson}/complete"

    for _ in range(2):  # twice on purpose: must not double count
        done = client.post(complete_url, headers=student["headers"])
        assert done.status_code == 200
        assert done.json()["completed"] is True

    progress = client.get(
        f"{API}/progress/courses/{built['course_id']}",
        headers=student["headers"],
    ).json()

    assert progress["total_lessons"] == 2
    assert progress["completed_lessons"] == 1
    assert progress["progress_percentage"] == 50.0
    assert progress["completed_lesson_ids"] == [first_lesson]
