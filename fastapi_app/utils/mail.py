import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException, status
from fastapi_app.schemas.auth_schemas import VerificationEmailSchema, FeedbackEmailSchema

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("MAIL_SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("MAIL_SENDER_PASSWORD")

async def send_message(email_data: VerificationEmailSchema) -> None:
    recipient_email = email_data.email
    verification_code = email_data.verification_code

    if not recipient_email or not verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required email data",
        )

    subject = f"Ваш код подтверждения Game Orbit - {verification_code}"
    template_path = os.path.join(os.path.dirname(__file__), "verification_email.html")
    with open(template_path, encoding="utf-8") as f:
        html_body = f.read().format(verification_code=verification_code)
    
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error sending email: {str(e)}",
        )
    
async def send_feedback_email(feedback_data: FeedbackEmailSchema):
    recipient_email = "info@gameorbit.kz"

    subject = f"{feedback_data.category} - {feedback_data.phone}"
    template_path = os.path.join(os.path.dirname(__file__), "feedback_email.html")
    with open(template_path, encoding="utf-8") as f:
        html_body = f.read().format(
            name=feedback_data.name,
            phone=feedback_data.phone,
            user_email=feedback_data.user_email,
            message=feedback_data.message
        )
    
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error sending email: {str(e)}",
        )