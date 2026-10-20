import uuid

from tests.helpers import API, build_course, make_user


def _course_payload(title=None):
    return {
        "title": title or f"Course {uuid.uuid4().hex[:6]}",
        "description": "A test course",
        "difficulty": "beginner",
    }


def test_list_courses_is_public(client):
    response = client.get(f"{API}/courses")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_course_requires_authentication(client):
    response = client.post(f"{API}/courses", json=_course_payload())

    assert response.status_code == 401


def test_student_cannot_create_course(client, db_session):
    student = make_user(client, db_session, "student")

    response = client.post(
        f"{API}/courses",
        headers=student["headers"],
        json=_course_payload(),
    )

    assert response.status_code == 403


def test_instructor_can_create_and_course_appears_in_list(client, db_session):
    instructor = make_user(client, db_session, "instructor")

    # Prime the cache first, to prove creating a course invalidates it.
    client.get(f"{API}/courses?limit=100")

    created = client.post(
        f"{API}/courses",
        headers=instructor["headers"],
        json=_course_payload("Cache Busting 101"),
    )

    assert created.status_code == 201
    assert created.json()["instructor_id"] == instructor["id"]

    listing = client.get(f"{API}/courses?limit=100").json()

    assert any(course["title"] == "Cache Busting 101" for course in listing)


def test_invalid_difficulty_is_rejected(client, db_session):
    instructor = make_user(client, db_session, "instructor")

    payload = _course_payload()
    payload["difficulty"] = "expert"

    response = client.post(
        f"{API}/courses",
        headers=instructor["headers"],
        json=payload,
    )

    assert response.status_code == 422


def test_overlong_title_is_a_422_not_a_500(client, db_session):
    instructor = make_user(client, db_session, "instructor")

    response = client.post(
        f"{API}/courses",
        headers=instructor["headers"],
        json=_course_payload("x" * 500),
    )

    assert response.status_code == 422


def test_pagination_limit(client, db_session):
    instructor = make_user(client, db_session, "instructor")

    for _ in range(3):
        client.post(
            f"{API}/courses",
            headers=instructor["headers"],
            json=_course_payload(),
        )

    page = client.get(f"{API}/courses?limit=2").json()

    assert len(page) == 2


def test_search_by_title(client, db_session):
    instructor = make_user(client, db_session, "instructor")
    needle = f"zebra{uuid.uuid4().hex[:6]}"

    client.post(
        f"{API}/courses",
        headers=instructor["headers"],
        json=_course_payload(f"Learning {needle}"),
    )

    results = client.get(f"{API}/courses?q={needle}").json()

    assert len(results) == 1
    assert needle in results[0]["title"]


def test_my_courses_only_returns_own(client, db_session):
    first = make_user(client, db_session, "instructor")
    second = make_user(client, db_session, "instructor")

    mine = client.post(
        f"{API}/courses",
        headers=first["headers"],
        json=_course_payload(),
    ).json()

    client.post(
        f"{API}/courses",
        headers=second["headers"],
        json=_course_payload(),
    )

    result = client.get(f"{API}/courses/mine", headers=first["headers"])

    assert result.status_code == 200
    assert [course["id"] for course in result.json()] == [mine["id"]]


def test_get_unknown_course_is_404(client):
    assert client.get(f"{API}/courses/2000000000").status_code == 404


def test_owner_can_update_but_others_cannot(client, db_session):
    owner = make_user(client, db_session, "instructor")
    other = make_user(client, db_session, "instructor")
    student = make_user(client, db_session, "student")
    admin = make_user(client, db_session, "admin")

    course = client.post(
        f"{API}/courses",
        headers=owner["headers"],
        json=_course_payload(),
    ).json()

    url = f"{API}/courses/{course['id']}"

    ok = client.put(url, headers=owner["headers"], json={"title": "Renamed"})
    assert ok.status_code == 200
    assert ok.json()["title"] == "Renamed"

    assert client.put(
        url, headers=other["headers"], json={"title": "Hijack"}
    ).status_code == 403

    assert client.put(
        url, headers=student["headers"], json={"title": "Hijack"}
    ).status_code == 403

    assert client.put(
        url, headers=admin["headers"], json={"title": "By admin"}
    ).status_code == 200


def test_owner_can_delete_course(client, db_session):
    owner = make_user(client, db_session, "instructor")
    other = make_user(client, db_session, "instructor")

    course = client.post(
        f"{API}/courses",
        headers=owner["headers"],
        json=_course_payload(),
    ).json()

    url = f"{API}/courses/{course['id']}"

    assert client.delete(url, headers=other["headers"]).status_code == 403
    assert client.delete(url, headers=owner["headers"]).status_code == 204
    assert client.get(url).status_code == 404


def test_other_instructor_cannot_add_modules(client, db_session):
    owner = make_user(client, db_session, "instructor")
    other = make_user(client, db_session, "instructor")

    built = build_course(client, owner)

    response = client.post(
        f"{API}/courses/{built['course_id']}/modules",
        headers=other["headers"],
        json={"title": "Not mine", "order": 9},
    )

    assert response.status_code == 403


def test_outline_lists_modules_and_lesson_titles_only(client, db_session):
    owner = make_user(client, db_session, "instructor")
    built = build_course(client, owner, lessons=2)

    outline = client.get(f"{API}/courses/{built['course_id']}/outline")

    assert outline.status_code == 200

    modules = outline.json()

    assert len(modules) == 1
    assert [lesson["id"] for lesson in modules[0]["lessons"]] == built["lesson_ids"]
    assert "content" not in modules[0]["lessons"][0]
