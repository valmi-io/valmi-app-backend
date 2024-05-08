import datetime
import json
import logging
import json
import os
from typing import List
import uuid
from decouple import config
import time
import json
from pydantic import Json
import requests


import psycopg2
from core.models import Account, Explore, Prompt, StorageCredentials, Workspace
from core.schemas import DetailSchema, ExploreSchema, ExploreSchemaIn, SyncStartStopSchemaIn
from ninja import Router
from core.services.explore_service import ExploreService
logger = logging.getLogger(__name__)

router = Router()
ACTIVATION_URL = config("ACTIVATION_SERVER")

@router.get("/workspaces/{workspace_id}", response={200: List[ExploreSchema], 400: DetailSchema})
def get_explores(request,workspace_id):
    try:
        logger.debug("listing explores")
        workspace = Workspace.objects.get(id=workspace_id)
        return Explore.objects.filter(workspace=workspace)
    except Exception:
        logger.exception("explores listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/create",response={200: ExploreSchema, 400: DetailSchema})
def create_explore(request, workspace_id,payload: ExploreSchemaIn):
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
        #create source
        source = ExploreService.create_source(workspace_id,account)
       #create destination
        spreadsheet_name = f"valmiio {prompt.name} sheet"
        destination_data = ExploreService.create_destination(spreadsheet_name,workspace_id,account)
        spreadsheet_url = destination_data[0]
        destination = destination_data[1]
        logger.debug("after service creation")
        logger.info(destination.id)
        #create sync
        sync = ExploreService.create_sync(source,destination,workspace_id)
        time.sleep(5)
        #creating explore
        data["name"] = f"valmiio {prompt.name}"
        data["sync"] = sync
        data["spreadsheet_url"] = spreadsheet_url
        explore =  Explore.objects.create(**data)
        #create run
        payload = SyncStartStopSchemaIn(full_refresh=True)
        ExploreService.create_run(request,workspace_id,sync.id,payload)
        return explore
    except Exception as e:
        logger.exception(e)
        return (400, {"detail": "The specific explore cannot be created."})
    

def custom_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    
@router.get("/workspaces/{workspace_id}/prompts/{prompt_id}/preview",response={200: Json, 404: DetailSchema})
def preview_data(request, workspace_id,prompt_id):
    prompt = Prompt.objects.get(id=prompt_id)
    storage_cred = StorageCredentials.objects.get(workspace_id=workspace_id)
    host_url = os.environ["DATA_WAREHOUSE_URL"]
    db_password = storage_cred.connector_config.get('password')
    db_username = storage_cred.connector_config.get('username')
    db_namespace = storage_cred.connector_config.get('namespace')
    conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
    cursor = conn.cursor()
    table = prompt.table
    # LOGIC for implementing pagination if necessary
    # query = f'SELECT COUNT(*) FROM {db_namespace}.{table}'
    # cursor.execute(query)
    # count_row = cursor.fetchone()
    # count = count_row[0] if count_row is not None else 0
    # page_id_int = int(page_id)

    # if page_id_int > count/25 or page_id_int<=0:
    #     return (404, {"detail": "Invalid page Id."})
    # skip = 25*(page_id_int-1)
    query = f'SELECT * FROM {db_namespace}.{table} LIMIT 100'
    cursor.execute(query)
    items = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor.fetchall()]
    return json.dumps(items, indent=4, default=custom_serializer)


@router.get("/workspaces/{workspace_id}/{explore_id}", response={200: ExploreSchema, 400: DetailSchema})
def get_explores(request,workspace_id,explore_id):
    try:
        logger.debug("listing explores")
        return Explore.objects.get(id=explore_id)
    except Exception:
        logger.exception("explore listing error")
        return (400, {"detail": "The  explore cannot be fetched."})


@router.get("/workspaces/{workspace_id}/{explore_id}/status", response={200: Json, 400: DetailSchema})
def get_explore_status(request,workspace_id,explore_id):
    try:
        logger.debug("getting_explore_status")
        explore = Explore.objects.get(id=explore_id)
        if explore.ready:
            return "sync completed"
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
        response = {}
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
