from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.pull_request import (
    PullRequest,
    PRCreate,
    PRMerge,
    PRReassign,
    PRResponse,
    PRReassignResponse,
    PullRequestReassignResult,
)
from app.schemas.error import ErrorResponse, ErrorCode
from app.services.pr_service import PRService

router = APIRouter()


@router.post(
    "/create",
    summary="Создать PR и автоматически назначить до 2 ревьюверов из команды автора",
    response_model=PRResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def create_pr(pr_in: PRCreate, db: AsyncSession = Depends(get_db)):
    pr, error = await PRService.create_pr(db, pr_in)
    if error:
        if error == ErrorCode.PR_EXISTS:
            return JSONResponse(status_code=409, content={"error": {"code": error, "message": "PR id already exists"}})
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "author not found"}})

    pr_dict = {
        "pull_request_id": pr.pull_request_id,
        "pull_request_name": pr.pull_request_name,
        "author_id": pr.author_id,
        "status": pr.status,
        "assigned_reviewers": [u.user_id for u in pr.reviewers],
        "createdAt": pr.created_at,
        "mergedAt": pr.merged_at,
    }
    return {"pr": pr_dict}


@router.post(
    "/merge",
    summary="Пометить PR как MERGED (идемпотентная операция)",
    response_model=PRResponse,
    responses={404: {"model": ErrorResponse}},
)
async def merge_pr(pr_in: PRMerge, db: AsyncSession = Depends(get_db)):
    pr, error = await PRService.merge_pr(db, pr_in.pull_request_id)
    if error:
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "PR not found"}})

    pr_dict = {
        "pull_request_id": pr.pull_request_id,
        "pull_request_name": pr.pull_request_name,
        "author_id": pr.author_id,
        "status": pr.status,
        "assigned_reviewers": [u.user_id for u in pr.reviewers],
        "createdAt": pr.created_at,
        "mergedAt": pr.merged_at,
    }
    return {"pr": pr_dict}


@router.post(
    "/reassign",
    summary="Переназначить конкретного ревьювера на другого из его команды",
    response_model=PRReassignResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def reassign_reviewer(reassign_in: PRReassign, db: AsyncSession = Depends(get_db)):
    pr, new_reviewer, error = await PRService.reassign_reviewer(
        db, reassign_in.pull_request_id, reassign_in.old_reviewer_id
    )
    if error:
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "PR or user not found"}})
        if error in [ErrorCode.PR_MERGED, ErrorCode.NOT_ASSIGNED, ErrorCode.NO_CANDIDATE]:
            return JSONResponse(status_code=409, content={"error": {"code": error, "message": "reassignment failed"}})

    pr_dict = {
        "pull_request_id": pr.pull_request_id,
        "pull_request_name": pr.pull_request_name,
        "author_id": pr.author_id,
        "status": pr.status,
        "assigned_reviewers": [u.user_id for u in pr.reviewers],
        "createdAt": pr.created_at,
    }
    return {"pr": pr_dict, "replaced_by": new_reviewer.user_id}
