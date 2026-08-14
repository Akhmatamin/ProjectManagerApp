import uuid

from app.shared.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.auth.models import RefreshToken
    from app.projects.models import Project



class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String,nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc),
                                                  onupdate=lambda: datetime.now(timezone.utc))

    user_projects : Mapped[List['Project']] = relationship('Project', back_populates='owner',
                                                           cascade='all, delete-orphan')
    members_projects : Mapped[List['Project']] = relationship(secondary='project_members', back_populates='members')

    user_tokens: Mapped[List['RefreshToken']] = relationship('RefreshToken', back_populates='token_user',
                                                             cascade='all, delete-orphan')






