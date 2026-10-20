import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.services.progress_service import get_course_progress
from app.worker import generate_certificate_notification


logger = logging.getLogger(__name__)


def _notify(student_email: str, certificate_number: str) -> None:
    """Queue the background notification. Never break the API if the queue
    (Redis/Celery) is down - the certificate itself is already saved."""
    try:
        generate_certificate_notification.delay(
            student_email,
            certificate_number,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not queue certificate notification: %s", exc)


def course_requirements_met(
    db: Session,
    student_id: int,
    course_id: int,
) -> bool:
    """A course is complete when every lesson is completed AND every quiz
    has been passed at least once."""
    progress = get_course_progress(db, student_id, course_id)

    quiz_count = (
        db.scalar(
            select(func.count(Quiz.id)).where(Quiz.course_id == course_id)
        )
        or 0
    )

    if progress["total_lessons"] == 0 and quiz_count == 0:
        return False

    if progress["completed_lessons"] < progress["total_lessons"]:
        return False

    passed_quizzes = (
        db.scalar(
            select(func.count(func.distinct(QuizAttempt.quiz_id)))
            .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
            .where(
                Quiz.course_id == course_id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.passed.is_(True),
            )
        )
        or 0
    )

    return passed_quizzes >= quiz_count


def get_certificate(
    db: Session,
    student_id: int,
    course_id: int,
) -> Certificate | None:
    return db.scalar(
        select(Certificate).where(
            Certificate.student_id == student_id,
            Certificate.course_id == course_id,
        )
    )


def issue_certificate_if_eligible(
    db: Session,
    student: User,
    course_id: int,
) -> tuple[Certificate | None, bool]:
    """Return (certificate, newly_created).

    Safe to call after every lesson completion / quiz attempt: it is
    idempotent, and the database unique constraint guarantees that two
    simultaneous requests cannot create two certificates.
    """
    existing = get_certificate(db, student.id, course_id)

    if existing is not None:
        return existing, False

    if not course_requirements_met(db, student.id, course_id):
        return None, False

    certificate = Certificate(
        certificate_number=f"CERT-{uuid.uuid4().hex[:12].upper()}",
        student_id=student.id,
        course_id=course_id,
    )

    db.add(certificate)

    try:
        db.commit()
    except IntegrityError:
        # Another request created it first - use theirs.
        db.rollback()
        return get_certificate(db, student.id, course_id), False

    db.refresh(certificate)

    _notify(student.email, certificate.certificate_number)

    return certificate, True
