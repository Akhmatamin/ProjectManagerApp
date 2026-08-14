import uuid
from app.shared.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_file import FileField
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.projects.models import Project



class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    file: Mapped[dict] = mapped_column(FileField)

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("projects.id"))
    project_document: Mapped['Project'] = relationship('Project', back_populates="documents")