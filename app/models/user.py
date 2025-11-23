from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import uuid


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.team_id"), nullable=True)

    team: Mapped["Team"] = relationship("Team", back_populates="members")

    @property
    def team_name(self) -> str | None:
        return self.team.team_name if self.team else None
