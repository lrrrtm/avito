from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.api.v1.endpoints import teams, users, pull_requests, stats, health
from app.db.session import engine
from app.db.base import Base
from app.models import team, user, pull_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="PR Reviewer Assignment Service (Test Task, Fall 2025, by lrrrtm)", version="1.0.0", lifespan=lifespan
)

app.include_router(teams.router, prefix="/team", tags=["Teams"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(pull_requests.router, prefix="/pullRequest", tags=["PullRequests"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(health.router, prefix="/health", tags=["Health"])
