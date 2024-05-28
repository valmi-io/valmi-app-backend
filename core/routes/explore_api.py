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
from core.services.prompts import PromptService

logger = logging.getLogger(__name__)

router = Router()
ACTIVATION_URL = config("ACTIVATION_SERVER")


@router.get("/workspaces/{workspace_id}/explores", response={200: List[ExploreSchemaOut], 500: DetailSchema})
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
            latest_sync_info = ExploreService.get_latest_sync_info(explore.sync.id)
            logger.debug(latest_sync_info)
            # checking whether run is created for explore or not
            if latest_sync_info.found == False:
                explore.enabled = False
                explore.sync_state = 'IDLE'
                explore.last_sync_result = 'UNKNOWN'
                continue
            explore.enabled = True
            # checking the run status
            if latest_sync_info.status == 'running':
                explore.sync_state = 'RUNNING'
                explore.last_sync_result = 'UNKNOWN'
            else:
                explore.last_sync_result = latest_sync_info.status.upper()
                explore.sync_state = 'IDLE'
            explore.last_sync_created_at = latest_sync_info.created_at
            # adding last successful sync info
            last_successful_sync_info = PromptService.is_sync_finished(explore.sync.id)
            if last_successful_sync_info.found == True:
                explore.last_sync_succeeded_at = last_successful_sync_info.run_end_at
            else:
                explore.last_sync_succeeded_at = ""
        return explores
    except Exception:
        logger.exception("explores listing error")
        return (500, {"detail": "The list of explores cannot be fetched."})


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
        response = ExploreService.create_run(request, workspace_id, sync.id, payload)
        logger.debug(response)
        return explore
    except Exception as e:
        logger.exception(e)
        return (400, {"detail": "The specific explore cannot be created."})


@router.get("/workspaces/{workspace_id}/explores/{explore_id}", response={200: ExploreSchema, 500: DetailSchema})
def get_explore_by_id(request, workspace_id, explore_id):
    try:
        logger.debug("listing explores")
        return Explore.objects.get(id=explore_id)
    except Exception:
        logger.exception("explore listing error")
        return (500, {"detail": "The  explore cannot be fetched."})
