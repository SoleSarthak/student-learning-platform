import uuid


def create_student(client):

    email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_list_courses(client):

    response = client.get("/api/v1/courses")

    assert response.status_code == 200

    assert isinstance(response.json(), list)


def test_create_course_requires_authentication(client):

    response = client.post(
        "/api/v1/courses",
        json={
            "title": "Test Course",
            "description": "A test course",
            "difficulty": "beginner",
        },
    )

    assert response.status_code == 401


def test_student_cannot_create_course(client):

    token = create_student(client)

    response = client.post(
        "/api/v1/courses",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Unauthorized Course",
            "description": "Students should not create courses",
            "difficulty": "beginner",
        },
    )

    assert response.status_code == 403