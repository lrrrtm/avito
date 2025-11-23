from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.pull_request import PullRequest
from app.schemas.error import ErrorCode


class UserService:
    @staticmethod
    async def set_is_active(db: AsyncSession, user_id: str, is_active: bool):
        result = await db.execute(select(User).options(selectinload(User.team)).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None, ErrorCode.NOT_FOUND

        user.is_active = is_active
        await db.commit()

        result = await db.execute(select(User).options(selectinload(User.team)).where(User.user_id == user_id))
        user = result.scalar_one()

        return user, None

    @staticmethod
    async def get_user_prs(db: AsyncSession, user_id: str):
        user_res = await db.execute(select(User).where(User.user_id == user_id))
        if not user_res.scalar_one_or_none():
            return None, ErrorCode.NOT_FOUND

        stmt = select(PullRequest).join(PullRequest.reviewers).where(User.user_id == user_id)
        result = await db.execute(stmt)
        prs = result.scalars().all()
        return prs, None
