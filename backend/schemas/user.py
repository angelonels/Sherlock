from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    
    class Config:
        from_attributes = True # Tells Pydantic to read SQLAlchemy objects seamlessly

class Token(BaseModel):
    access_token: str
    token_type: str
