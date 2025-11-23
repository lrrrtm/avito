from pydantic import BaseModel
from typing import List


class UserStats(BaseModel):
    user_id: str
    review_count: int


class PRStats(BaseModel):
    pull_request_id: str
    reviewer_count: int


class StatsResponse(BaseModel):
    users: List[UserStats]
    prs: List[PRStats]
