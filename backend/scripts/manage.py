"""Small admin CLI. Run from the `backend/` folder:

    python -m scripts.manage seed                       # demo users + sample course
    python -m scripts.manage set-role you@mail.com instructor

Why this exists: public sign-up only creates *students* (so nobody can make
themselves an admin). Use `set-role` to promote a real account, or `seed`
to get a ready-made demo.
"""
import argparse
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import SessionLocal

# Import every model so SQLAlchemy can resolve all relationships.
from app.models import (  # noqa: F401
    certificate,
    course,
    enrollment,
    lesson,
    module,
    progress,
    question,
    quiz,
    quiz_attempt,
    user,
)
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import CourseModule
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User


DEMO_PASSWORD = "DemoPass123!"
VALID_ROLES = ("student", "instructor", "admin")

DEMO_USERS = [
    ("Demo Admin", "admin@example.com", "admin"),
    ("Demo Instructor", "instructor@example.com", "instructor"),
    ("Demo Student", "student@example.com", "student"),
]

SAMPLE_COURSE = {
    "title": "Python for Beginners",
    "description": (
        "Learn Python from scratch: variables, data types, control flow "
        "and functions, with a short quiz after each part."
    ),
    "difficulty": "beginner",
    "modules": [
        {
            "title": "Getting started",
            "lessons": [
                (
                    "What is Python?",
                    "Python is a beginner-friendly programming language used "
                    "for websites, data science, automation and more.\n\n"
                    "You write instructions in plain text files that end in "
                    ".py and run them with the python command.",
                ),
                (
                    "Variables and data types",
                    "A variable is a name that points to a value.\n\n"
                    "  age = 21\n  name = \"Sarthak\"\n  is_student = True\n\n"
                    "The common basic types are int, float, str and bool.",
                ),
            ],
        },
        {
            "title": "Control flow and functions",
            "lessons": [
                (
                    "If statements and loops",
                    "Use if / elif / else to make decisions and for / while "
                    "to repeat work.\n\n"
                    "  for i in range(3):\n      print(i)\n",
                ),
                (
                    "Writing functions",
                    "A function packages code so you can reuse it.\n\n"
                    "  def greet(name):\n      return f\"Hello, {name}!\"\n",
                ),
            ],
        },
    ],
    "quiz": {
        "title": "Python basics quiz",
        "passing_score": 60,
        "questions": [
            (
                "Which keyword defines a function in Python?",
                ("func", "def", "function", "lambda"),
                "B",
            ),
            (
                "What is the type of the value 3.14?",
                ("int", "str", "float", "bool"),
                "C",
            ),
            (
                "What does range(3) produce?",
                ("1, 2, 3", "0, 1, 2", "0, 1, 2, 3", "3 only"),
                "B",
            ),
            (
                "Which file extension do Python scripts use?",
                (".pt", ".py", ".python", ".pyt"),
                "B",
            ),
        ],
    },
}


def _get_or_create_user(db, name, email, role):
    existing = db.scalar(select(User).where(User.email == email))

    if existing:
        existing.role = role
        return existing

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        role=role,
    )
    db.add(new_user)
    db.flush()

    return new_user


def seed() -> None:
    if settings.is_production:
        sys.exit("Refusing to seed demo accounts when ENVIRONMENT=production.")

    with SessionLocal() as db:
        users = {
            role: _get_or_create_user(db, name, email, role)
            for name, email, role in DEMO_USERS
        }

        already = db.scalar(
            select(Course).where(Course.title == SAMPLE_COURSE["title"])
        )

        if already:
            db.commit()
            print("Sample course already exists - nothing more to do.")
        else:
            course_row = Course(
                title=SAMPLE_COURSE["title"],
                description=SAMPLE_COURSE["description"],
                difficulty=SAMPLE_COURSE["difficulty"],
                instructor_id=users["instructor"].id,
            )
            db.add(course_row)
            db.flush()

            lesson_order = 0
            for module_order, module_data in enumerate(
                SAMPLE_COURSE["modules"], start=1
            ):
                module_row = CourseModule(
                    title=module_data["title"],
                    order=module_order,
                    course_id=course_row.id,
                )
                db.add(module_row)
                db.flush()

                for title, content in module_data["lessons"]:
                    lesson_order += 1
                    db.add(
                        Lesson(
                            title=title,
                            content=content,
                            order=lesson_order,
                            module_id=module_row.id,
                        )
                    )

            quiz_data = SAMPLE_COURSE["quiz"]
            quiz_row = Quiz(
                title=quiz_data["title"],
                passing_score=quiz_data["passing_score"],
                course_id=course_row.id,
            )
            db.add(quiz_row)
            db.flush()

            for text, options, correct in quiz_data["questions"]:
                db.add(
                    Question(
                        question_text=text,
                        option_a=options[0],
                        option_b=options[1],
                        option_c=options[2],
                        option_d=options[3],
                        correct_answer=correct,
                        quiz_id=quiz_row.id,
                    )
                )

            db.commit()
            print("Created sample course with 4 lessons and a 4-question quiz.")

    print("\nDemo accounts (password for all: %s)" % DEMO_PASSWORD)
    for _name, email, role in DEMO_USERS:
        print(f"  {role:<10} {email}")


def set_role(email: str, role: str) -> None:
    if role not in VALID_ROLES:
        sys.exit(f"Role must be one of: {', '.join(VALID_ROLES)}")

    with SessionLocal() as db:
        target = db.scalar(select(User).where(User.email == email.lower()))

        if target is None:
            sys.exit(f"No user with email {email}")

        target.role = role
        db.commit()

    print(f"{email} is now a(n) {role}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Admin helper commands")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="Create demo users and a sample course")

    role_parser = sub.add_parser("set-role", help="Change a user's role")
    role_parser.add_argument("email")
    role_parser.add_argument("role", choices=VALID_ROLES)

    args = parser.parse_args()

    if args.command == "seed":
        seed()
    elif args.command == "set-role":
        set_role(args.email, args.role)


if __name__ == "__main__":
    main()
