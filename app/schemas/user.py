from typing import List
from pydantic import BaseModel
from app.schemas.pull_request import PullRequestShort


class UserUpdateActive(BaseModel):
    user_id: str
    is_active: bool


class User(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: User


class UserReviewsResponse(BaseModel):
    user_id: str
    pull_requests: List[PullRequestShort]
