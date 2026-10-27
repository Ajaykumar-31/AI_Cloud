from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class UserMe(BaseModel):
    email: EmailStr
    role: str
