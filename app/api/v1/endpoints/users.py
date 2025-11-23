from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import User, UserUpdateActive, UserResponse, UserReviewsResponse
from app.schemas.pull_request import PullRequestShort
from app.schemas.error import ErrorResponse, ErrorCode
from app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/setIsActive",
    summary="Установить флаг активности пользователя",
    response_model=UserResponse,
    responses={404: {"model": ErrorResponse}},
)
async def set_is_active(user_in: UserUpdateActive, db: AsyncSession = Depends(get_db)):
    user, error = await UserService.set_is_active(db, user_in.user_id, user_in.is_active)
    if error:
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "user not found"}})
    return {"user": user}


@router.get(
    "/getReview",
    summary="Получить PR'ы, где пользователь назначен ревьювером",
    response_model=UserReviewsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_user_reviews(user_id: str, db: AsyncSession = Depends(get_db)):
    prs, error = await UserService.get_user_prs(db, user_id)
    if error:
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "user not found"}})
    return {"user_id": user_id, "pull_requests": prs}
