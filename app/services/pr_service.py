import random
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.pull_request import PullRequest
from app.models.user import User
from app.models.team import Team
from app.schemas.pull_request import PRCreate
from app.schemas.error import ErrorCode


class PRService:
    @staticmethod
    async def create_pr(db: AsyncSession, pr_in: PRCreate):
        result = await db.execute(select(PullRequest).where(PullRequest.pull_request_id == pr_in.pull_request_id))
        if result.scalar_one_or_none():
            return None, ErrorCode.PR_EXISTS

        result = await db.execute(select(User).where(User.user_id == pr_in.author_id))
        author = result.scalar_one_or_none()
        if not author:
            return None, ErrorCode.NOT_FOUND  # Author not found

        stmt = select(User).where(
            User.team_id == author.team_id, User.user_id != author.user_id, User.is_active == True
        )
        result = await db.execute(stmt)
        candidates = result.scalars().all()

        reviewers = []
        if len(candidates) <= 2:
            reviewers = list(candidates)
        else:
            reviewers = random.sample(candidates, 2)

        db_pr = PullRequest(
            pull_request_id=pr_in.pull_request_id,
            pull_request_name=pr_in.pull_request_name,
            author_id=pr_in.author_id,
            status="OPEN",
            created_at=datetime.utcnow(),
            reviewers=reviewers,
        )
        db.add(db_pr)
        await db.commit()

        stmt = (
            select(PullRequest)
            .options(selectinload(PullRequest.reviewers))
            .where(PullRequest.pull_request_id == pr_in.pull_request_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one(), None

    @staticmethod
    async def merge_pr(db: AsyncSession, pull_request_id: str):
        stmt = (
            select(PullRequest)
            .options(selectinload(PullRequest.reviewers))
            .where(PullRequest.pull_request_id == pull_request_id)
        )
        result = await db.execute(stmt)
        pr = result.scalar_one_or_none()

        if not pr:
            return None, ErrorCode.NOT_FOUND

        if pr.status != "MERGED":
            pr.status = "MERGED"
            pr.merged_at = datetime.utcnow()
            await db.commit()
            await db.refresh(pr)

        return pr, None

    @staticmethod
    async def reassign_reviewer(db: AsyncSession, pull_request_id: str, old_user_id: str):
        stmt = (
            select(PullRequest)
            .options(selectinload(PullRequest.reviewers))
            .where(PullRequest.pull_request_id == pull_request_id)
        )
        result = await db.execute(stmt)
        pr = result.scalar_one_or_none()

        if not pr:
            return None, None, ErrorCode.NOT_FOUND  # PR not found

        if pr.status == "MERGED":
            return None, None, ErrorCode.PR_MERGED

        old_reviewer = next((r for r in pr.reviewers if r.user_id == old_user_id), None)
        if not old_reviewer:
            user_res = await db.execute(select(User).where(User.user_id == old_user_id))
            if not user_res.scalar_one_or_none():
                return None, None, ErrorCode.NOT_FOUND

            return None, None, ErrorCode.NOT_ASSIGNED

        current_reviewer_ids = [r.user_id for r in pr.reviewers]

        stmt = select(User).where(
            User.team_id == old_reviewer.team_id,
            User.is_active == True,
            User.user_id != pr.author_id,
            User.user_id.notin_(current_reviewer_ids),
        )
        result = await db.execute(stmt)
        candidates = result.scalars().all()

        if not candidates:
            return None, None, ErrorCode.NO_CANDIDATE

        new_reviewer = random.choice(candidates)

        pr.reviewers.remove(old_reviewer)
        pr.reviewers.append(new_reviewer)

        await db.commit()
        await db.refresh(pr)

        return pr, new_reviewer, None
