from celery import Celery

from app.database import setting

celery_app = Celery(
    "tasks", broker=setting.redis_celery_url, backend=setting.redis_celery_url
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Kyiv",
    enable_utc=True,
)


@celery_app.task(name="send_booking_email")
def send_booking_email(email: str, booking_id: int):
    print(f"Отправка подтверждения для брони №{booking_id} на почту {email}...")
    return f"Email sent to {email}"
