"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Friday, March 17th 2023, 6:09:16 pm
Author: Rajashekar Varkala @ valmi.io

"""

from datetime import datetime
from typing import Dict, Optional

from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema, Schema
from pydantic import UUID4

from .models import Account, Connector, Credential, Destination, Explore, Organization, Package, Prompt, Source, Sync, Workspace, OAuthApiKeys


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
        model_fields = ["first_name", "email","username"]

    organizations: list[OrganizationSchema] = None


class CreatedUserSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = User
        model_fields = ["first_name", "email","username"]
    organizations: OrganizationSchema = Field(None, alias="organization")
    auth_token: str
    

class ConnectorSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Connector
        model_fields = ["type", "docker_image", "docker_tag", "display_name", "oauth", "oauth_keys", "mode"]


class PackageSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Package
        model_fields = ["name","gated","scopes"]

class PromptSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Prompt
        model_fields = ["id","name","description","query","parameters","package_id","gated","table"]


class ConnectorConfigSchemaIn(Schema):
    config: Dict


class CreateConfigSchemaIn(Schema):
    config: Dict


class SyncStartStopSchemaIn(Schema):
    full_refresh: bool = False


class CredentialSchemaIn(Schema):
    connector_type: str
    connector_config: Dict
    account: Dict = None
    name: str

class ExploreSchemaIn(Schema):
    ready: bool = False
    name:str
    account: Dict = None
    prompt_id:str
    refresh_token:str

class ExplorePreviewDataIn(Schema):
    prompt_id:str


class CredentialSchemaUpdateIn(Schema):
    id: UUID4
    connector_type: str
    connector_config: Dict
    account: Dict = None
    name: str


class AccountSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Account
        model_fields = ["name", "external_id", "meta_data", "id", "profile"]


class CredentialSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Credential
        model_fields = ["connector_config", "id", "name"]

    connector_type: str = Field(None, alias="connector.type")
    docker_image: str = Field(None, alias="connector.docker_image")
    docker_tag: str = Field(None, alias="connector.docker_tag")
    display_name: str = Field(None, alias="connector.display_name")
    oauth: str = Field(None, alias="connector.oauth")
    oauth_keys: str = Field(None, alias="connector.oauth_keys")
    mode: list = Field(None, alias="connector.mode")
    account: AccountSchema = Field(None, alias="account")


class ExploreSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Explore
        model_fields = ["ready", "name", "spreadsheet_url", "account", "id"]
    account: AccountSchema = Field(None, alias="account")
    prompt: PromptSchema = Field(None, alias="prompt")
    workspace: WorkspaceSchema = Field(None, alias="workspace")



class BaseSchemaIn(Schema):
    workspace_id: UUID4


class SourceSchemaIn(Schema):
    credential_id: UUID4
    name: str
    catalog: Dict


class SourceSchema(ModelSchema):
    credential: CredentialSchema = None  # ! None - to mark it as optional

    class Config(CamelSchemaConfig):
        model = Source
        model_fields = ["name", "catalog", "id"]


class DestinationSchemaIn(Schema):
    credential_id: UUID4
    name: str
    catalog: Dict


class DestinationSchema(ModelSchema):
    credential: CredentialSchema = None  # ! None - to mark it as optional

    class Config(CamelSchemaConfig):
        model = Destination
        model_fields = ["name", "catalog", "id"]


class SyncSchemaIn(Schema):
    name: str
    source_id: UUID4
    destination_id: UUID4
    schedule: Dict
    ui_state: Optional[Dict]


class SyncSchemaUpdateIn(Schema):
    id: UUID4
    name: str
    source_id: UUID4
    destination_id: UUID4
    schedule: Dict
    ui_state: Optional[Dict]


class SyncSchema(ModelSchema):
    source: SourceSchema = None  # ! None - to mark it as optional
    destination: DestinationSchema = None

    class Config(CamelSchemaConfig):
        model = Sync
        model_fields = ["name", "id", "source", "destination", "schedule", "status", "ui_state"]


class SyncRunSchema(Schema):
    sync_id: UUID4
    run_id: UUID4
    run_at: datetime
    status: str
    metrics: Optional[Dict]
    extra: Optional[Dict]


class SyncIdSchema(Schema):
    sync_id: UUID4


class DetailSchema(Schema):
    detail: str


class SuccessSchema(Schema):
    status: str = "success"


class FailureSchema(Schema):
    status: str = "failure"


class GenericJsonSchema(Schema):
    class Config(Schema.Config):
        extra = "allow"

    pass


class OAuthSchemaIn(Schema):
    type: str
    oauth_config: Dict


class OAuthSchemaUpdateIn(Schema):
    type: str
    oauth_config: Dict


class OAuthSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = OAuthApiKeys
        model_fields = ["workspace", "type", "oauth_config"]


class SocialAccount(Schema):
    provider: str    
    type: str
    access_token: str
    expires_at: int
    refresh_token: str
    scope: str
    token_type: str
    id_token: str
class SocialUser(Schema):
    name: str
    email: str
class SocialAuthLoginSchema(Schema):
    account: SocialAccount
    user: SocialUser
