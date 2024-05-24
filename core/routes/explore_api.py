import asyncio
import logging
from typing import List
import uuid
from decouple import config
from core.models import Account, Explore, Prompt, Workspace
from core.schemas.schemas import DetailSchema, SyncStartStopSchemaIn
from core.schemas.explore import ExploreSchema, ExploreSchemaIn, ExploreSchemaOut
from ninja import Router

from core.models import Account, Explore, Prompt, Workspace
from core.services.explore import ExploreService

logger = logging.getLogger(__name__)

router = Router()
ACTIVATION_URL = config("ACTIVATION_SERVER")


@router.get("/workspaces/{workspace_id}/explores", response={200: List[ExploreSchemaOut], 400: DetailSchema})
def get_explores(request, workspace_id):
    try:
        logger.debug("listing explores")
        workspace = Workspace.objects.get(id=workspace_id)
        explores = Explore.objects.filter(workspace=workspace).order_by('created_at')
        for explore in explores:
            explore.prompt_id = str(explore.prompt.id)
            explore.description = Prompt.objects.get(id=explore.prompt.id).description
            explore.workspace_id = str(explore.workspace.id)
            explore.id = str(explore.id)
            explore.sync_id = str(explore.sync.id)
            explore_sync_status = ExploreService.is_sync_created_or_running(explore.sync.id)
            if explore_sync_status.get('enabled') == False:
                explore.enabled = False
                explore.sync_state = 'IDLE'
                explore.last_sync_result = 'UNKNOWN'
                explore.last_sync_created_at = ""
                explore.last_sync_succeeded_at = ""
                continue
            explore.enabled = True
            if explore_sync_status.get('is_running') == True:
                explore.sync_state = 'RUNNING'
                explore.last_sync_result = 'UNKNOWN'
            else:
                explore.last_sync_result = explore_sync_status.get('status').upper()
                explore.sync_state = 'IDLE'
            explore.last_sync_created_at = explore_sync_status.get('created_at')
            explore.last_sync_succeeded_at = ExploreService.get_last_sync_successful_time(explore.sync.id)
        return explores
    except Exception:
        logger.exception("explores listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/explores/create", response={200: ExploreSchema, 400: DetailSchema})
def create_explore(request, workspace_id, payload: ExploreSchemaIn):
    data = payload.dict()
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        prompt = Prompt.objects.get(id=data["prompt_id"])
        data["prompt"] = prompt
        account_info = data.pop("account", None)
        account = {}
        if account_info and len(account_info) > 0:
            account_info["id"] = uuid.uuid4()
            account_info["workspace"] = data["workspace"]
            account = Account.objects.create(**account_info)
            data["account"] = account
        # create source
        source = ExploreService.create_source(
            data["prompt_id"], data["schema_id"], data["time_window"], data["filters"], workspace_id, account)
       # create destination
        spreadsheet_name = f"valmi.io {prompt.name} sheet"
        destination_data = ExploreService.create_destination(spreadsheet_name, workspace_id, account)
        spreadsheet_url = destination_data[0]
        destination = destination_data[1]
        # create sync
        sync = ExploreService.create_sync(source, destination, workspace_id)
        # creating explore
        del data["schema_id"]
        del data["filters"]
        del data["time_window"]
        # data["name"] = f"valmiio {prompt.name}"
        data["sync"] = sync
        data["ready"] = False
        data["spreadsheet_url"] = spreadsheet_url
        explore = Explore.objects.create(**data)
        # create run
        asyncio.run(ExploreService.wait_for_run(5))
        payload = SyncStartStopSchemaIn(full_refresh=False)
        ExploreService.create_run(request, workspace_id, sync.id, payload)
        return explore
    except Exception as e:
        logger.exception(e)
        return (400, {"detail": "The specific explore cannot be created."})


@router.get("/workspaces/{workspace_id}/explores/{explore_id}", response={200: ExploreSchema, 400: DetailSchema})
def get_explores(request, workspace_id, explore_id):
    try:
        logger.debug("listing explores")
        return Explore.objects.get(id=explore_id)
    except Exception:
        logger.exception("explore listing error")
        return (400, {"detail": "The  explore cannot be fetched."})
