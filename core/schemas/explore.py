from typing import Dict
from ninja import Field, ModelSchema, Schema
from core.models import Explore
from core.schemas.prompt import Filter, TimeWindow
from core.schemas.schemas import AccountSchema, CamelSchemaConfig, PromptSchema, WorkspaceSchema


class ExploreSchemaOut(Schema):
    ready:bool
    name:str
    spreadsheet_url:str
    id:str
    prompt_id:str
    workspace_id:str
    last_successful_time:str
    created_at:str

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
    account: Dict = None
    prompt_id: str
    schema_id: str
    time_window: TimeWindow
    filters: list[Filter]
