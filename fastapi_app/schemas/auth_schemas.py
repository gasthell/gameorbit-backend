from pydantic import BaseModel, EmailStr

class AuthLogin(BaseModel):
    email: str
    password: str
    remember: bool

class AuthRegister(BaseModel):
    username: str
    phone: str
    email: EmailStr
    password: str

class VerificationEmailSchema(BaseModel):
    email: EmailStr
    verification_code: str

class ResendVerificationEmailSchema(BaseModel):
    email: EmailStr

class FeedbackEmailSchema(BaseModel):
    name: str
    phone: str
    user_email: str
    message: str
    category: str

class UpdateProfileSchema(BaseModel):
    username: str
    phone: str
    email: EmailStr