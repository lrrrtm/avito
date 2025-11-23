from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PRStatus(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class PRCreate(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class PRMerge(BaseModel):
    pull_request_id: str


class PRReassign(BaseModel):
    pull_request_id: str
    old_reviewer_id: str


class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: List[str]
    createdAt: Optional[datetime] = None
    mergedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class PullRequestReassignResult(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: List[str]
    createdAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class PRResponse(BaseModel):
    pr: PullRequest


class PRReassignResponse(BaseModel):
    pr: PullRequestReassignResult
    replaced_by: str


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus

    class Config:
        from_attributes = True
