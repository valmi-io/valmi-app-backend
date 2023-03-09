from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema, Schema
from pydantic import UUID4, Json

from .models import Connector, Credential, Destination, Organization, Source, Sync, Workspace

User = get_user_model()


def camel_to_snake(s):
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


class CamelSchemaConfig(Schema.Config):
    alias_generator = camel_to_snake
    allow_population_by_field_name = True


class WorkspaceSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Workspace
        model_fields = "__all__"


class OrganizationSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Organization
        model_fields = "__all__"

    workspaces: list[WorkspaceSchema] = None


class UserSchemaOut(ModelSchema):
    class Config(CamelSchemaConfig):
        model = User
        model_fields = ["first_name", "email"]

    organizations: list[OrganizationSchema] = None


class ConnectorSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Connector
        model_fields = ["type", "docker_image", "docker_tag", "display_name"]


class CredentialSchemaIn(Schema):
    connector_type: str
    connector_config: Json
    name: str


class CredentialSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Credential
        model_fields = ["connector_config", "id"]

    connector_type: str = Field(None, alias="connector.type")


class BaseSchemaIn(Schema):
    workspace_id: UUID4


class SourceSchemaIn(Schema):
    credential_id: UUID4
    name: str
    catalog: Json


class SourceSchema(ModelSchema):
    credential: CredentialSchema = None  # ! None - to mark it as optional

    class Config(CamelSchemaConfig):
        model = Source
        model_fields = ["name", "catalog", "id"]


class DestinationSchemaIn(Schema):
    credential_id: UUID4
    name: str
    catalog: Json


class DestinationSchema(ModelSchema):
    credential: CredentialSchema = None  # ! None - to mark it as optional

    class Config(CamelSchemaConfig):
        model = Destination
        model_fields = ["name", "catalog", "id"]


class SyncSchemaIn(Schema):
    name: str
    source_id: UUID4
    destination_id: UUID4
    schedule: Json


class SyncSchema(ModelSchema):
    source: SourceSchema = None  # ! None - to mark it as optional
    destination: DestinationSchema = None

    class Config(CamelSchemaConfig):
        model = Sync
        model_fields = ["name", "id", "source", "destination", "schedule"]


class SyncIdSchema(Schema):
    sync_id: UUID4


class DetailSchema(Schema):
    detail: str


class SuccessSchema(Schema):
    status: str = "success"


class FailureSchema(Schema):
    status: str = "failure"
