import asyncio
import logging
import uuid
from typing import List

from decouple import config
from ninja import Router

from core.models import Account, Explore, Prompt, Workspace
from core.schemas.explore import (ExploreSchema, ExploreSchemaIn,
                                  ExploreSchemaOut)
from core.schemas.schemas import DetailSchema, SyncStartStopSchemaIn
from core.services.explore import ExploreService
from core.services.prompts import PromptService
from django.db import transaction
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
            # as we are using full_refresh as true in explore creation enable only if previous sync got succeded
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
                if latest_sync_info.status == 'success':
                    explore.last_sync_succeeded_at = latest_sync_info.created_at
            explore.last_sync_created_at = latest_sync_info.created_at
            # adding last successful sync info
            last_successful_sync_info = PromptService.is_sync_finished(explore.sync.id)
            if last_successful_sync_info.found == True:
                explore.last_sync_succeeded_at = last_successful_sync_info.run_end_at
        return explores
    except Exception:
        logger.exception("explores listing error")
        return (500, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/explores/create", response={200: ExploreSchema, 400: DetailSchema})
def create_explore(request, workspace_id, payload: ExploreSchemaIn):
    data = payload.dict()
    logger.debug(data)
    try:
        with transaction.atomic():
            try:
                table_name = ExploreService.validate_explore_name(data["name"], workspace_id)
            except Exception as err:
                logger.exception(err)
                message = str(err)
                return (400, {"detail": message})
            # chceck if sheet_url is not emoty check for necessary permissions to write into file
            if data["sheet_url"] is not None:
                try:
                    if not ExploreService.is_sheet_accessible(data["sheet_url"], workspace_id):
                        return (400, {"detail": "You dont have access or missing write access to the spreadsheet"})
                except Exception as err:
                    logger.exception(err)
                    message = str(err)
                    return (400, {"detail": message})
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
                table_name, data["prompt_id"], data["schema_id"], data["time_window"], data["filters"], data["time_grain"], workspace_id, account)
        # create destination
            spreadsheet_title = f"valmi.io {prompt.name} sheet"
            destination_data = ExploreService.create_destination(
                spreadsheet_title, data["name"], data["sheet_url"], workspace_id, account)
            spreadsheet_url = destination_data[0]
            destination = destination_data[1]
            # creating the sync
            sync = ExploreService.create_sync(data["name"], source, destination, workspace_id)
            logger.debug("After sync")
            # creating explore
            del data["schema_id"]
            del data["filters"]
            del data["time_window"]
            del data["sheet_url"]
            del data["time_grain"]
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
        return (500, {"detail": "The  explore cannot be fetched."})
