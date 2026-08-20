import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.base import Base

if TYPE_CHECKING:
    from app.documents.models import Document
    from app.users.models import User


class ProjectPermission(str, PyEnum):
    READ = "read"
    WRITE = "write"


class ProjectMember(Base):
    __tablename__ = "project_members"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True)

    permission: Mapped[ProjectPermission] = mapped_column(SQLEnum(ProjectPermission,
                                                                  values_callable=lambda x: [e.value for e in x]),
                                                          default=ProjectPermission.READ, nullable=False)
    user: Mapped['User'] = relationship('User', back_populates="project_memberships")
    project: Mapped['Project'] = relationship('Project', back_populates="user_memberships")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id"))  
    owner: Mapped['User'] = relationship('User', back_populates="user_projects")


    user_memberships: Mapped[list['ProjectMember']] = relationship('ProjectMember', back_populates='project',
                                                                   cascade="all, delete-orphan")


    documents: Mapped[list['Document']] = relationship('Document', back_populates="project_document",
                                                       cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(UTC),
                                                  onupdate=lambda: datetime.now(UTC))
