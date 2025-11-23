from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.pull_request import pr_reviewers


class StatsService:
    @staticmethod
    async def get_stats(db: AsyncSession):
        # reviews per user
        stmt_users = select(pr_reviewers.c.user_id, func.count(pr_reviewers.c.pull_request_id).label("count")).group_by(
            pr_reviewers.c.user_id
        )

        result_users = await db.execute(stmt_users)
        user_stats = [{"user_id": row.user_id, "review_count": row.count} for row in result_users]

        # reviewers per PR
        stmt_prs = select(pr_reviewers.c.pull_request_id, func.count(pr_reviewers.c.user_id).label("count")).group_by(
            pr_reviewers.c.pull_request_id
        )

        result_prs = await db.execute(stmt_prs)
        pr_stats = [{"pull_request_id": row.pull_request_id, "reviewer_count": row.count} for row in result_prs]

        return {"users": user_stats, "prs": pr_stats}
