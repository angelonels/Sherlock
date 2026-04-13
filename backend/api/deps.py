from fastapi import Depends
from models.user import User
from utils.auth import get_current_user


async def current_user(user: User = Depends(get_current_user)) -> User:
    return user
