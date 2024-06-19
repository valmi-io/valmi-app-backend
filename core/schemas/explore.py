from datetime import datetime
from typing import Dict, Optional

from ninja import Field, ModelSchema, Schema

from core.models import Explore
from core.schemas.prompt import Filter, TimeGrain, TimeWindow
from core.schemas.schemas import (AccountSchema, CamelSchemaConfig,
                                  PromptSchema, WorkspaceSchema)


class ExploreSchemaOut(Schema):
    ready: bool
    name: str
    spreadsheet_url: str
    id: str
    prompt_id: str
    enabled: bool
    description: str
    workspace_id: str
    last_sync_succeeded_at: Optional[datetime] = None
    last_sync_created_at: Optional[datetime] = None
    last_sync_result: str
    sync_state: str
    sync_id: str


class ExploreSchema(ModelSchema):
    class Config(CamelSchemaConfig):
        model = Explore
        model_fields = ["ready", "name", "spreadsheet_url", "account", "id"]
    account: AccountSchema = Field(None, alias="account")
    prompt: PromptSchema = Field(None, alias="prompt")
    workspace: WorkspaceSchema = Field(None, alias="workspace")


class ExploreStatusIn(Schema):
    sync_id: str


class ExploreSchemaIn(Schema):
    name: str
    sheet_url: Optional[str]
    account: Dict = None
    prompt_id: str
    schema_id: str
    time_window: TimeWindow
    filters: list[Filter]
    time_grain: Optional[TimeGrain] = None


class LatestSyncInfo(Schema):
    found: bool
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    found: bool
    status: Optional[str] = None
    created_at: Optional[datetime] = None
