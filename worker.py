import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import Celery

from database import setting

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
def send_booking_email(
    email: str,
    room: str,
    date_from: date,
    date_to: date,
    total_price: float,
    booking_id: int,
):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = setting.email
    smtp_password = setting.smtp_password

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = email
    msg["Subject"] = f"Успешное бронирование №{booking_id} 🎉"

    body = f"""
    Здравствуйте!
    
    Ваша бронь с {date_from} до {date_to} на номер {room} была успешно подтверждена.
    С вашего баланса было списано {total_price} токенов.
    
    Ждем вас!
    """

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()

        server.login(smtp_user, smtp_password)

        server.send_message(msg)
        server.quit()

        return "Email sent successfully"

    except Exception as e:
        return f"Failed to send: {e}"
