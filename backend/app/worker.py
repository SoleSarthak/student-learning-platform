import logging

from celery import Celery

from app.core.config import settings


logger = logging.getLogger(__name__)


celery_app = Celery(
    "student_learning_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(
    name="certificates.send_notification",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_certificate_notification(
    student_email: str,
    certificate_number: str,
) -> dict:
    """Runs in the background worker after a certificate is issued.

    Today it only logs. Swap the body for a real email provider
    (SendGrid, SES, SMTP) without touching the API code.
    """
    logger.info(
        "Certificate notification for %s (certificate=%s)",
        student_email,
        certificate_number,
    )

    return {
        "status": "notification generated",
        "email": student_email,
        "certificate_number": certificate_number,
    }
