import json
import logging
import json
import time
from typing import List
import uuid
from decouple import config
import json
from pydantic import Json
import requests
from core.models import Account, Explore, Prompt, Workspace
from core.schemas.schemas import DetailSchema, ExploreSchema, ExploreSchemaIn, SyncStartStopSchemaIn
from ninja import Router
from core.services.explore_service import ExploreService
logger = logging.getLogger(__name__)

router = Router()
ACTIVATION_URL = config("ACTIVATION_SERVER")


@router.get("/workspaces/{workspace_id}", response={200: List[ExploreSchema], 400: DetailSchema})
def get_explores(request, workspace_id):
    try:
        logger.debug("listing explores")
        workspace = Workspace.objects.get(id=workspace_id)
        return Explore.objects.filter(workspace=workspace).order_by('created_at')
    except Exception:
        logger.exception("explores listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/create", response={200: ExploreSchema, 400: DetailSchema})
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
        source = ExploreService.create_source(data["schema_id"], data["query"], workspace_id, account)
        time.sleep(6)
       # create destination
        spreadsheet_name = f"valmiio {prompt.name} sheet"
        destination_data = ExploreService.create_destination(spreadsheet_name, workspace_id, account)
        spreadsheet_url = destination_data[0]
        destination = destination_data[1]
        # create sync
        sync = ExploreService.create_sync(source, destination, workspace_id)
        # await asyncio.sleep(5)
        time.sleep(5)
        # creating explore
        del data["schema_id"]
        del data["query"]
        data["name"] = f"valmiio {prompt.name}"
        data["sync"] = sync
        data["ready"] = False
        data["spreadsheet_url"] = spreadsheet_url
        explore = Explore.objects.create(**data)
        # create run
        payload = SyncStartStopSchemaIn(full_refresh=True)
        ExploreService.create_run(request, workspace_id, sync.id, payload)
        return explore
    except Exception as e:
        logger.exception(e)
        return (400, {"detail": "The specific explore cannot be created."})


@router.get("/workspaces/{workspace_id}/{explore_id}", response={200: ExploreSchema, 400: DetailSchema})
def get_explore(request, workspace_id, explore_id):
    try:
        logger.debug("listing explores")
        return Explore.objects.get(id=explore_id)
    except Exception:
        logger.exception("explore listing error")
        return (400, {"detail": "The  explore cannot be fetched."})


@router.get("/workspaces/{workspace_id}/{explore_id}/status", response={200: Json, 400: DetailSchema})
def get_explore_status(request, workspace_id, explore_id):
    try:
        logger.debug("getting_explore_status")
        explore = Explore.objects.get(id=explore_id)
        response = {}
        if explore.ready:
            response["status"] = "success"
            return json.dumps(response)
        sync_id = explore.sync.id
        response = requests.get(f"{ACTIVATION_URL}/syncs/{sync_id}/latestRunStatus")
        status = response.text
        print(status)
        # if status == 'stopped':
        #     CODE for re running the sync from backend
        #     payload = SyncStartStopSchemaIn(full_refresh=True)
        #     response = create_new_run(request,workspace_id,sync_id,payload)
        #     print(response)
        #     return "sync got failed. Please re-try again"
        if status == '"running"':
            response["status"] = "running"
            return json.dumps(response)
        if status == '"failed"':
            response["status"] = "failed"
            return json.dumps(response)
        explore.ready = True
        explore.save()
        response["status"] = "success"
        return json.dumps(response)
    except Exception:
        logger.exception("get_explore_status error")
        return (400, {"detail": "The  explore cannot be fetched."})
