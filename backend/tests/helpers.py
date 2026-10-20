import uuid

from sqlalchemy import update

from app.models.user import User


PASSWORD = "TestPassword123"
API = "/api/v1"


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_user(client, db_session, role: str = "student") -> dict:
    """Register + (optionally) promote + log in. Returns id, email, headers."""
    email = unique_email(role)

    response = client.post(
        f"{API}/auth/register",
        json={"name": f"Test {role}", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text

    user_id = response.json()["id"]

    if role != "student":
        db_session.execute(
            update(User).where(User.id == user_id).values(role=role)
        )
        db_session.commit()

    login = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    return {
        "id": user_id,
        "email": email,
        "token": token,
        "headers": auth(token),
    }


def build_course(
    client,
    instructor: dict,
    lessons: int = 2,
    questions: int = 2,
    passing_score: int = 50,
) -> dict:
    """Create course -> module -> lessons -> quiz -> questions (all answer 'A')."""
    headers = instructor["headers"]

    course = client.post(
        f"{API}/courses",
        headers=headers,
        json={
            "title": f"Course {uuid.uuid4().hex[:6]}",
            "description": "A course for testing",
            "difficulty": "beginner",
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    module = client.post(
        f"{API}/courses/{course_id}/modules",
        headers=headers,
        json={"title": "Module 1", "order": 1},
    )
    assert module.status_code == 201, module.text
    module_id = module.json()["id"]

    lesson_ids = []
    for index in range(lessons):
        lesson = client.post(
            f"{API}/modules/{module_id}/lessons",
            headers=headers,
            json={
                "title": f"Lesson {index + 1}",
                "content": "Lesson content",
                "order": index + 1,
            },
        )
        assert lesson.status_code == 201, lesson.text
        lesson_ids.append(lesson.json()["id"])

    quiz = client.post(
        f"{API}/quizzes/courses/{course_id}",
        headers=headers,
        json={"title": "Quiz", "passing_score": passing_score},
    )
    assert quiz.status_code == 201, quiz.text
    quiz_id = quiz.json()["id"]

    question_ids = []
    for index in range(questions):
        question = client.post(
            f"{API}/quizzes/{quiz_id}/questions",
            headers=headers,
            json={
                "question_text": f"Question {index + 1}?",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "a",  # lowercase on purpose: API normalises
            },
        )
        assert question.status_code == 201, question.text
        question_ids.append(question.json()["id"])

    return {
        "course_id": course_id,
        "module_id": module_id,
        "lesson_ids": lesson_ids,
        "quiz_id": quiz_id,
        "question_ids": question_ids,
    }


def answers(question_ids, letter: str = "A") -> dict:
    return {
        "answers": [
            {"question_id": question_id, "answer": letter}
            for question_id in question_ids
        ]
    }
