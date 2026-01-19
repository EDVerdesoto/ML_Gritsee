from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class UserPublic(BaseModel):
    username: str
    is_active: bool
    class Config:
        from_attributes = True  