"""fix timestamp defaults, add FK indexes, one certificate per student+course

Revision ID: e7b1c4a92f10
Revises: 35e88d6c15dc
Create Date: 2026-10-12 12:00:00.000000

Why this migration exists
-------------------------
1. The initial schema used server_default='now()' (a quoted string literal).
   PostgreSQL can resolve that literal ONCE, when the table is created, so
   every row would get the same timestamp. We switch to the real now()
   function, evaluated on every insert.
2. Foreign-key columns we filter/join on had no index.
3. Nothing stopped two certificates for the same student + course
   (e.g. two quiz submissions racing each other).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b1c4a92f10"
down_revision: Union[str, Sequence[str], None] = "35e88d6c15dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIMESTAMP_COLUMNS = [
    ("users", "created_at"),
    ("courses", "created_at"),
    ("certificates", "issued_at"),
    ("enrollments", "enrolled_at"),
    ("quiz_attempts", "attempted_at"),
]

INDEXES = [
    ("ix_courses_instructor_id", "courses", "instructor_id"),
    ("ix_modules_course_id", "modules", "course_id"),
    ("ix_lessons_module_id", "lessons", "module_id"),
    ("ix_quizzes_course_id", "quizzes", "course_id"),
    ("ix_questions_quiz_id", "questions", "quiz_id"),
    ("ix_quiz_attempts_student_id", "quiz_attempts", "student_id"),
    ("ix_quiz_attempts_quiz_id", "quiz_attempts", "quiz_id"),
    ("ix_lesson_progress_lesson_id", "lesson_progress", "lesson_id"),
    ("ix_enrollments_course_id", "enrollments", "course_id"),
]


def upgrade() -> None:
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=sa.text("now()"),
        )

    for name, table, column in INDEXES:
        op.create_index(name, table, [column], unique=False)

    # Remove accidental duplicates (keep the oldest) before adding the rule.
    op.execute(
        """
        DELETE FROM certificates a
        USING certificates b
        WHERE a.student_id = b.student_id
          AND a.course_id = b.course_id
          AND a.id > b.id
        """
    )

    op.create_unique_constraint(
        "unique_student_course_certificate",
        "certificates",
        ["student_id", "course_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "unique_student_course_certificate",
        "certificates",
        type_="unique",
    )

    for name, table, _column in reversed(INDEXES):
        op.drop_index(name, table_name=table)

    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default="now()",
        )
