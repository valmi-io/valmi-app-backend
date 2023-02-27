from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema
from pydantic import UUID4

from .models import Credential, Destination, Organization, Source, Sync, Workspace

User = get_user_model()


def to_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


class OrganizationSchema(ModelSchema):
    class Config:
        alias_generator = to_camel
        model = Organization
        model_fields = "__all__"


class WorkspaceSchema(ModelSchema):
    class Config:
        alias_generator = to_camel
        model = Workspace
        model_fields = "__all__"

    organization: list[OrganizationSchema] = None


class UserSchemaOut(ModelSchema):
    class Config:
        alias_generator = to_camel
        model = User
        model_fields = "__all__"

    organizations: list[OrganizationSchema] = None


class CredentialSchema(ModelSchema):
    class Config:
        alias_generator = to_camel
        model = Credential
        model_fields = "__all__"


class BaseSchemaIn(Schema):
    workspace_id: UUID4


class SourceSchema(ModelSchema):
    credential: CredentialSchema = None  # ! None - to mark it as optional

    class Config:
        alias_generator = to_camel
        model = Source
        model_fields = "__all__"


class DestinationSchema(ModelSchema):
    credential: CredentialSchema = None  # ! None - to mark it as optional

    class Config:
        alias_generator = to_camel
        model = Destination
        model_fields = "__all__"


class SyncSchema(ModelSchema):
    source: SourceSchema = None  # ! None - to mark it as optional
    destination: DestinationSchema = None

    class Config:
        alias_generator = to_camel
        model = Sync
        model_fields = "__all__"
