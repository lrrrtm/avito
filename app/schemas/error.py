from pydantic import BaseModel
from enum import Enum


class ErrorCode(str, Enum):
    DEMO_ERROR = "ERROR_CODE"
    TEAM_EXISTS = "TEAM_EXISTS"
    USER_EXISTS = "USER_EXISTS"
    PR_EXISTS = "PR_EXISTS"
    PR_MERGED = "PR_MERGED"
    NOT_ASSIGNED = "NOT_ASSIGNED"
    NO_CANDIDATE = "NO_CANDIDATE"
    NOT_FOUND = "NOT_FOUND"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
