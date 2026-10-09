from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "student_learning_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery_app.task
def generate_certificate_notification(
    student_email: str,
    certificate_number: str,
):
    print(
        f"Certificate notification generated "
        f"for {student_email} "
        f"certificate={certificate_number}"
    )

    return {
        "status": "notification generated",
        "email": student_email,
        "certificate_number": certificate_number,
    }


@celery_app.task
def process_course_completion(
    student_id: int,
    course_id: int,
):
    print(
        f"Processing course completion "
        f"student={student_id} course={course_id}"
    )

    return {
        "status": "course completion processed",
        "student_id": student_id,
        "course_id": course_id,
    }