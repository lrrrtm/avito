from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import uuid


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    team_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    members: Mapped[list["User"]] = relationship("User", back_populates="team", cascade="all, delete-orphan")
