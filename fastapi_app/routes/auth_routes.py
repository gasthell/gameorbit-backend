from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends, Form
from fastapi_app.schemas.auth_schemas import AuthRegister, VerificationEmailSchema, AuthLogin, ResendVerificationEmailSchema
import random
from fastapi_app.utils.mail import send_message
from django.db import IntegrityError
import django
import os
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth import authenticate
from django.core.cache import cache
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import re
from PIL import Image  # Add this import

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameorbit.settings")
django.setup()
from core.models import User
from fastapi import File, UploadFile

router = APIRouter()

MAX_LOGIN_ATTEMPTS = 10
LOGIN_ATTEMPT_TIMEOUT = 60 * 30  # 30 minutes

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "3e4794f01904fd69957d56d51f8221e3640e300ed6452f72fe530ce35495fd95")
ALGORITHM = "HS256"

security = HTTPBearer()

def clean_email(email):
    # Remove dots and +extension from the local part
    local, at, domain = email.partition('@')
    local = re.sub(r'\.', '', local)
    local = re.sub(r'\+.*', '', local)
    return f"{local}@{domain}"

@router.post("/login/")
def login(data: AuthLogin):
    email = clean_email(data.email.lower())
    cache_key = f"login_attempts:{email}"
    attempts = cache.get(cache_key, 0)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
    user = authenticate(username=email, password=data.password)
    if not user:
        cache.set(cache_key, attempts + 1, LOGIN_ATTEMPT_TIMEOUT)
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified.")
    cache.delete(cache_key)
    # Set token expiration based on rememberMe
    remember = data.remember
    if remember:
        exp_seconds = 60 * 60 * 24 * 30  # 30 days
    else:
        exp_seconds = 60 * 60 * 24  # 1 day
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow().timestamp() + exp_seconds
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/signup/")
def register(data: AuthRegister, background_tasks: BackgroundTasks):
    verification_code = str(random.randint(100000, 999999))
    email = clean_email(data.email.lower())
    now = timezone.now()
    try:
        user = User.objects.create_user(
            email=email,
            phone=data.phone,
            password=data.password,
            name=data.username,
            is_verified=False,
            verification_code=verification_code,
            verification_code_created=now
        )
    except IntegrityError:
        user = User.objects.filter(email=email).first()
        if user and not user.is_verified:
            user.verification_code = verification_code
            user.verification_code_created = now
            user.save()
            email_data = VerificationEmailSchema(email=data.email, verification_code=verification_code)
            background_tasks.add_task(send_message, email_data)
            return {"message": "Verification code resent to email"}
        return {"error": "User with this email already exists"}
    email_data = VerificationEmailSchema(email=data.email, verification_code=verification_code)
    background_tasks.add_task(send_message, email_data)
    return {"message": "Verification code sent to email"}

@router.post("/verify-email/")
def verify_email(data: VerificationEmailSchema):
    email = clean_email(data.email.lower())
    try:
        user = User.objects.get(email=email, verification_code=data.verification_code)
    except User.DoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid verification code or email.")
    if not user.verification_code_created or timezone.now() > user.verification_code_created + timedelta(minutes=30):
        raise HTTPException(status_code=400, detail="Verification code expired. Please request a new one.")
    user.is_verified = True
    user.verification_code = None
    user.verification_code_created = None
    user.save()
    return {"message": "Email verified successfully."}

@router.get("/user/")
def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
        user = User.objects.get(id=user_id)
        # Return all user info (customize as needed)
        return {
            "id": user.id,
            "username": user.name,
            "email": user.email,
            "phone": user.phone,
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
            "subscription": user.subscription_id,
            "end_date": user.end_date,
            "free_trial": user.free_trial,
            "linked_game_ids": user.linked_game_ids,
            "sessions": user.sessions,
            "active": user.active,
            "role": user.role,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "date_joined": user.date_joined,
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

@router.post("/resend-verification/")
def resend_verification(data: ResendVerificationEmailSchema, background_tasks: BackgroundTasks):
    email = clean_email(data.email.lower())
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email is already verified.")
    verification_code = str(random.randint(100000, 999999))
    user.verification_code = verification_code
    user.verification_code_created = timezone.now()
    user.save()
    email_data = VerificationEmailSchema(email=email, verification_code=verification_code)
    background_tasks.add_task(send_message, email_data)
    return {"message": "Verification code resent to email."}

@router.patch("/user/update-profile/")
def update_profile(
    email: str = Form(...),
    username: str = Form(...),
    phone: str = Form(...),
    profile_image: UploadFile = File(None),
    current_password: str = Form(None),
    new_password: str = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
        user = User.objects.get(id=user_id)
        # Update user fields
        user.email = clean_email(email.lower())
        user.name = username
        user.phone = phone
        # Handle password change
        if current_password and new_password:
            if not user.check_password(current_password):
                raise HTTPException(status_code=400, detail="Wrong password")
            user.set_password(new_password)
        # Handle profile image upload
        if profile_image:
            dir_path = "images/users"
            os.makedirs(dir_path, exist_ok=True)
            file_path = f"{dir_path}/{user_id}.jpg"
            # Compress, resize, and save image
            image = Image.open(profile_image.file)
            image = image.convert("RGB")  # Ensure compatibility
            image.thumbnail((512, 512))  # Resize to max 512x512, keeping aspect ratio
            image.save(file_path, format="JPEG", quality=70, optimize=True)
            user.profile_picture = file_path
        user.save()
        return {"message": "Profile updated successfully."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))