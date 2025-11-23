from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, tuple_
from sqlalchemy.orm import selectinload
from app.models.team import Team
from app.models.user import User
from app.models.pull_request import PullRequest, pr_reviewers
from app.schemas.team import TeamCreate, TeamDeactivateRequest
from app.schemas.error import ErrorCode
import random
import uuid


class TeamService:
    @staticmethod
    async def create_team(db: AsyncSession, team_in: TeamCreate):
        result = await db.execute(select(Team).where(Team.team_name == team_in.team_name))
        db_team = result.scalar_one_or_none()

        if not db_team:
            db_team = Team(team_name=team_in.team_name)
            db.add(db_team)
            await db.flush()  # Get team_id

        for member in team_in.members:
            result_user = await db.execute(select(User).where(User.user_id == member.user_id))
            db_user = result_user.scalar_one_or_none()

            if db_user:
                if db_user.team_id and db_user.team_id != db_team.team_id:
                    return None, ErrorCode.USER_EXISTS

                db_user.username = member.username
                db_user.is_active = member.is_active
                if not db_user.team_id:
                    db_user.team_id = db_team.team_id
            else:
                db_user = User(
                    user_id=member.user_id,
                    username=member.username,
                    is_active=member.is_active,
                    team_id=db_team.team_id,
                )
                db.add(db_user)

        await db.commit()

        stmt = select(Team).options(selectinload(Team.members)).where(Team.team_name == team_in.team_name)
        result = await db.execute(stmt)
        return result.scalar_one(), None

    @staticmethod
    async def get_team(db: AsyncSession, team_name: str):
        stmt = select(Team).options(selectinload(Team.members)).where(Team.team_name == team_name)
        result = await db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            return None, ErrorCode.NOT_FOUND
        return team, None

    @staticmethod
    async def mass_deactivate_members(db: AsyncSession, team_id: uuid.UUID, user_ids: list[str]):
        stmt_replacements = select(User).where(
            User.team_id == team_id, User.is_active == True, User.user_id.not_in(user_ids)
        )
        replacements_res = await db.execute(stmt_replacements)
        replacement_ids = [u.user_id for u in replacements_res.scalars().all()]

        await db.execute(update(User).where(User.user_id.in_(user_ids)).values(is_active=False))

        stmt_assignments = (
            select(pr_reviewers.c.pull_request_id, pr_reviewers.c.user_id, PullRequest.author_id)
            .join(PullRequest, PullRequest.pull_request_id == pr_reviewers.c.pull_request_id)
            .where(pr_reviewers.c.user_id.in_(user_ids), PullRequest.status == "OPEN")
        )
        assignments_res = await db.execute(stmt_assignments)
        assignments = assignments_res.all()

        if not assignments:
            return

        affected_pr_ids = list(set(a.pull_request_id for a in assignments))

        stmt_current_reviewers = select(pr_reviewers.c.pull_request_id, pr_reviewers.c.user_id).where(
            pr_reviewers.c.pull_request_id.in_(affected_pr_ids)
        )
        curr_rev_res = await db.execute(stmt_current_reviewers)

        current_reviewers_map = {}
        for pr_id, u_id in curr_rev_res.all():
            if pr_id not in current_reviewers_map:
                current_reviewers_map[pr_id] = set()
            current_reviewers_map[pr_id].add(u_id)

        deletes = []
        inserts = []

        for pr_id, old_user_id, author_id in assignments:
            deletes.append((pr_id, old_user_id))

            current_revs = current_reviewers_map.get(pr_id, set())

            candidates = [uid for uid in replacement_ids if uid != author_id and uid not in current_revs]

            if candidates:
                new_reviewer_id = random.choice(candidates)
                inserts.append({"pull_request_id": pr_id, "user_id": new_reviewer_id})
                current_reviewers_map[pr_id].add(new_reviewer_id)

        if deletes:
            await db.execute(
                delete(pr_reviewers).where(tuple_(pr_reviewers.c.pull_request_id, pr_reviewers.c.user_id).in_(deletes))
            )

        if inserts:
            await db.execute(pr_reviewers.insert(), inserts)

    @staticmethod
    async def deactivate_users(db: AsyncSession, deactivate_in: TeamDeactivateRequest):
        result = await db.execute(select(Team).where(Team.team_name == deactivate_in.team_name))
        team = result.scalar_one_or_none()

        if not team:
            return ErrorCode.NOT_FOUND

        await TeamService.mass_deactivate_members(db, team.team_id, deactivate_in.user_ids)

        await db.commit()
        return None
