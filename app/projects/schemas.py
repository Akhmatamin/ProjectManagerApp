import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserSchemaMeta(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class ProjectCreateSchema(BaseModel):
    name: str
    description: str
    members_ids: list[uuid.UUID] = []

    model_config = ConfigDict(from_attributes=True)

class DocumentsListSchema(BaseModel):
    id: uuid.UUID
    file: dict | None
    project_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ProjectsListSchema(BaseModel):
    id: uuid.UUID = Field(serialization_alias='project_id')
    name: str
    description: str
    owner_id: uuid.UUID
    owner: UserSchemaMeta
    members: list[UserSchemaMeta]
    documents: list[DocumentsListSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    members: list[uuid.UUID] | None = None
    documents: list[uuid.UUID] | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadSchema(BaseModel):
    file: str
    project_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class DocumentsListSchema(BaseModel):
    id: uuid.UUID
    file: dict | None
    project_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ProjectCreatedSchema(BaseModel):
    project_id: uuid.UUID = Field(validation_alias='id')
    name: str
    description: str
    owner: UserSchemaMeta
    members: list[UserSchemaMeta]
    documents: list[DocumentsListSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailsSchema(ProjectCreatedSchema):
    pass



