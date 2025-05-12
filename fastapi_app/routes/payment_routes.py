from fastapi import APIRouter, status
from fastapi_app.schemas.auth_schemas import FeedbackEmailSchema
from fastapi_app.utils.mail import send_feedback_email

router = APIRouter()

@router.post("/send-feedback/", status_code=status.HTTP_200_OK)
async def send_feedback(feedback: FeedbackEmailSchema):
    await send_feedback_email(feedback)
    return {"message": "Feedback sent successfully"}