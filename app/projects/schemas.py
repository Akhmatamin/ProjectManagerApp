import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class UserSchemaMeta(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class ProjectCreateSchema(BaseModel):
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)

class DocumentsListSchema(BaseModel):
    id: uuid.UUID
    file: dict | None
    project_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


def _extract_members(value):
    if not isinstance(value, list):
        return value
    return [member.user if hasattr(member, "user") else member for member in value]


class ProjectsListSchema(BaseModel):
    id: uuid.UUID = Field(serialization_alias='project_id')
    name: str
    description: str
    owner_id: uuid.UUID
    owner: UserSchemaMeta
    members: list[UserSchemaMeta] = Field(validation_alias="user_memberships")
    documents: list[DocumentsListSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_date(self, date: datetime):
        return date.strftime("%d-%m-%Y %H:%M:%S")

    @field_validator("members", mode="before")
    @classmethod
    def parse_members_from_memberships(cls, value):
        return _extract_members(value)


class ProjectUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    # members: list[uuid.UUID] | None = None
    # documents: list[uuid.UUID] | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadSchema(BaseModel):
    file: str
    project_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ProjectCreatedSchema(BaseModel):
    project_id: uuid.UUID = Field(validation_alias='id')
    name: str
    description: str
    owner: UserSchemaMeta
    members: list[UserSchemaMeta] = Field(validation_alias="user_memberships")
    documents: list[DocumentsListSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_date(self, date: datetime):
        return date.strftime("%d-%m-%Y %H:%M:%S")

    @field_validator("members", mode="before")
    @classmethod
    def parse_members_from_memberships(cls, value):
        return _extract_members(value)


class ProjectDetailsSchema(ProjectCreatedSchema):
    pass


class UserReadSchema(BaseModel):
    id : uuid.UUID
    email: str
    first_name: str
    last_name: str
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("joined_at")
    def serialize_date(self, date: datetime):
        return date.strftime("%d-%m-%Y %H:%M:%S")

class ProjectReadSchema(BaseModel):
    id: uuid.UUID
    description: str | None
    owner_id: uuid.UUID
    members: list[UserSchemaMeta] = Field(validation_alias="user_memberships")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_date(self, date: datetime):
        return date.strftime("%d-%m-%Y %H:%M:%S")

    @field_validator("members", mode="before")
    @classmethod
    def parse_members_from_memberships(cls, value):
        return _extract_members(value)


class InviteMemberResponse(BaseModel):
    message: str
    project_id: uuid.UUID


