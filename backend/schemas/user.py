from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    
    class Config:
        from_attributes = True # Tells Pydantic to read SQLAlchemy objects seamlessly

class Token(BaseModel):
    access_token: str
    token_type: str
