from datetime import datetime
import json
import logging
import os
from typing import List
import uuid

import psycopg2
from pydantic import Json
from core.models import Account, Explore, Prompt, StorageCredentials, Workspace
from core.schemas import DetailSchema, ExplorePreviewDataIn, ExploreSchema, ExploreSchemaIn
from ninja import Router

logger = logging.getLogger(__name__)

router = Router()

@router.get("/workspaces/{workspace_id}", response={200: List[ExploreSchema], 400: DetailSchema})
def get_prompts(request,workspace_id):
    try:
        logger.debug("listing connectors")
        workspace = Workspace.objects.get(id=workspace_id)
        explores = Explore.objects.filter(workspace=workspace)
        return explores
    except Exception:
        logger.exception("explores listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/create",response={200: ExploreSchema, 400: DetailSchema})
def create_explore(request, workspace_id,payload: ExploreSchemaIn):
    logger.info("data before creating")
    data = payload.dict()
    logger.info("data before creating")
    logger.info(data)
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["prompt"] = Prompt.objects.get(id=data["prompt_id"])
        account_info = data.pop("account", None)
        if account_info and len(account_info) > 0:
            account_info["id"] = uuid.uuid4()
            account_info["workspace"] = data["workspace"]
            data["account"] = Account.objects.create(**account_info)
        logger.debug(data)
        explore = Explore.objects.create(**data)
        return explore
    except Exception:
        logger.exception("explore creation error")
        return (400, {"detail": "The specific explore cannot be created."})
    
@router.get("/workspaces/{workspace_id}/preview-data",response={200: Json, 400: DetailSchema})
def create_sync(request, workspace_id,payload: ExplorePreviewDataIn):
    data = payload.dict()
    logger.info("data before creating")
    logger.info(data)
    prompt = Prompt.objects.get(id=data["prompt_id"])
    storage_cred = StorageCredentials.objects.get(workspace_id=workspace_id)
    host_url = os.environ["DB_URL"]
    db_password = storage_cred.connector_config.get('password')
    db_username = storage_cred.connector_config.get('username')
    conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
    cursor = conn.cursor()
    query = prompt.query
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        d = {}
        for i, col in enumerate(cursor.description):
            for i, col in enumerate(cursor.description):
            # Convert datetime objects to ISO format
                if isinstance(row[i], datetime):
                    d[col[0]] = row[i].isoformat()
                else:
                    d[col[0]] = row[i]
            result.append(d)

    # Convert the list of dictionaries to JSON and print it
    json_result = json.dumps(result)
    print(json_result)
    return json_result