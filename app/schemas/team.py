from pydantic import BaseModel
from typing import List


class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    team_name: str
    members: List[TeamMember]


class Team(TeamCreate):
    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    team: Team


class TeamDeactivateRequest(BaseModel):
    team_name: str
    user_ids: List[str]
