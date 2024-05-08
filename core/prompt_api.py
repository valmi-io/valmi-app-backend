import datetime
import json
import logging
import os
from typing import List

import psycopg2
from ninja import Router
from pydantic import Json

from core.models import Credential, Prompt, StorageCredentials
from core.schemas.prompt import PromptPreviewSchemaIn
from core.schemas.schemas import DetailSchema, PromptSchema, PromptSchemaOut
from core.services.prompts import PromptService

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: List[PromptSchemaOut], 400: DetailSchema})
def get_prompts(request):
    try:
        prompts = list(Prompt.objects.all().values())
        connector_ids = list(Credential.objects.values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        for prompt in prompts:
            prompt["id"]  = str(prompt["id"])
            if prompt["type"] in connector_types:
                prompt["enabled"] = True
            else:
                prompt["enabled"] = False
        return prompts
    except Exception as err:
        logger.exception("prompts listing error:"+ err)
        return (400, {"detail": "The list of prompts cannot be fetched."})

@router.get("/{prompt_id}", response={200: PromptSchema, 400: DetailSchema})
def get_prompts(request,prompt_id):
    try:
        logger.debug("listing prompts")
        prompt = Prompt.objects.get(id=prompt_id)
        return prompt
    except Exception:
        logger.exception("prompt listing error")
        return (400, {"detail": "The  prompt cannot be fetched."})

    
def custom_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    
@router.get("/workspaces/{workspace_id}/prompts/{prompt_id}/preview",response={200: Json, 404: DetailSchema})
def preview_data(request, workspace_id,prompt_id, prompt_req: PromptPreviewSchemaIn):
    prompt = Prompt.objects.get(id=prompt_id)
    query = PromptService().build(prompt.table, prompt_req.time_window, prompt_req.filters)
    storage_cred = StorageCredentials.objects.get(workspace_id=workspace_id)
    host_url = os.environ["DATA_WAREHOUSE_URL"]
    db_password = storage_cred.connector_config.get('password')
    db_username = storage_cred.connector_config.get('username')
    db_namespace = storage_cred.connector_config.get('namespace')
    conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
    cursor = conn.cursor()
    cursor.execute(query)
    items = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor.fetchall()]
    return json.dumps(items, indent=4, default=custom_serializer)
