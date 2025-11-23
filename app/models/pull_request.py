from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

pr_reviewers = Table(
    "pr_reviewers",
    Base.metadata,
    Column("pull_request_id", ForeignKey("pull_requests.pull_request_id"), primary_key=True),
    Column("user_id", ForeignKey("users.user_id"), primary_key=True),
)


class PullRequest(Base):
    __tablename__ = "pull_requests"

    pull_request_id: Mapped[str] = mapped_column(String, primary_key=True)
    pull_request_name: Mapped[str] = mapped_column(String)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    status: Mapped[str] = mapped_column(String, default="OPEN")  # OPEN, MERGED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    author: Mapped["User"] = relationship("User")
    reviewers: Mapped[list["User"]] = relationship("User", secondary=pr_reviewers)
