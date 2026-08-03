import uuid

from app.shared.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_file import FileField, File
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.auth.models import RefreshToken

project_members = Table('project_members', Base.metadata,
                        Column('user_id', ForeignKey('users.id'), primary_key=True),
                        Column('project_id', ForeignKey('projects.id'), primary_key=True),
)


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
    members_projects : Mapped[List['Project']] = relationship(secondary=project_members, back_populates='members')

    user_tokens: Mapped[List['RefreshToken']] = relationship('RefreshToken', back_populates='token_user',
                                                             cascade='all, delete-orphan')



class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id"))
    owner: Mapped['User'] = relationship('User', back_populates="user_projects")

    members: Mapped[List['User']] = relationship('User', secondary=project_members, back_populates="members_projects")
    documents: Mapped[List['Document']] = relationship('Document', back_populates="project_document",
                                                       cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc),
                                                  onupdate=lambda: datetime.now(timezone.utc))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    file: Mapped[File] = mapped_column(FileField)

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("projects.id"))
    project_document: Mapped['Project'] = relationship('Project', back_populates="documents")


