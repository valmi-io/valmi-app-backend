import datetime
import json
import logging
import os
from typing import List
from ninja import Router
import psycopg2
from pydantic import Json
from core.models import Credential, Prompt, Source, StorageCredentials
from core.schemas.prompt import PromptPreviewSchemaIn
from core.schemas.schemas import DetailSchema, PromptByIdSchema
from core.services.prompts import PromptService

from core.models import Prompt, StorageCredentials
from core.schemas.schemas import DetailSchema, PromptSchemaOut

logger = logging.getLogger(__name__)
router = Router()


@router.get("/workspaces/{workspace_id}/prompts", response={200: List[PromptSchemaOut], 400: DetailSchema})
def get_prompts(request, workspace_id):
    try:
        prompts = list(Prompt.objects.all().values())
        connector_ids = list(Credential.objects.values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        for prompt in prompts:
            prompt["id"] = str(prompt["id"])
            if prompt["type"] in connector_types:
                prompt["enabled"] = True
            else:
                prompt["enabled"] = False
        return prompts
    except Exception as err:
        logger.exception("prompts listing error:" + err)
        return (400, {"detail": "The list of prompts cannot be fetched."})


@router.get("/workspaces/{workspace_id}/prompts/{prompt_id}", response={200: PromptByIdSchema, 400: DetailSchema})
def get_prompt(request, workspace_id, prompt_id):
    try:
        logger.debug("listing prompts")
        prompt = Prompt.objects.get(id=prompt_id)
        if not PromptService.is_prompt_enabled(workspace_id, prompt):
            detail_message = f"The prompt is not enabled. Please add '{prompt.type}' connector"
            return 400, {"detail": detail_message}
        credential_info = Source.objects.filter(
            credential__workspace_id=workspace_id,
            credential__connector_id=prompt.type
        ).select_related('credential', 'source_access_info')
        schemas = {}

        for info in credential_info:
            if source_access_info := info.source_access_info.first():
                storage_id = source_access_info.storage_credentials.id
                if storage_id not in schemas:
                    schema = {
                        "id": str(storage_id),
                        "name": source_access_info.storage_credentials.connector_config["schema"],
                        "sources": [],
                    }
                    schemas[storage_id] = schema
                schemas[storage_id]["sources"].append({
                    "name": f"{info.credential.name}${info.credential.created_at}",
                    "id": str(info.id),
                })
        # Convert schemas dictionary to a list (optional)
        final_schemas = list(schemas.values())
        prompt.schemas = final_schemas
        logger.debug(prompt)
        return prompt
    except Exception:
        logger.exception("prompt listing error")
        return (400, {"detail": "The  prompt cannot be fetched."})


def custom_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()


@router.post("/workspaces/{workspace_id}/prompts/{prompt_id}/preview", response={200: Json, 400: DetailSchema})
def preview_data(request, workspace_id, prompt_id, prompt_req: PromptPreviewSchemaIn):
    try:
        prompt = Prompt.objects.get(id=prompt_id)
        if not PromptService.is_prompt_enabled(workspace_id, prompt):
            detail_message = f"The prompt is not enabled. Please add '{prompt.type}' connector"
            return 400, {"detail": detail_message}
        storage_credentials = StorageCredentials.objects.get(id=prompt_req.schema_id)
        schema_name = storage_credentials.connector_config["schema"]
        table_name = f'{schema_name}.{prompt.table}'
        query = PromptService().build(table_name, prompt_req.time_window, prompt_req.filters)
        logger.debug(query)
        host_url = os.environ["DATA_WAREHOUSE_URL"]
        db_password = storage_credentials.connector_config.get('password')
        db_username = storage_credentials.connector_config.get('username')
        conn = psycopg2.connect(host=host_url, port="5432", database="dvdrental",
                                user=db_username, password=db_password)
        cursor = conn.cursor()
        cursor.execute(query)
        items = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor.fetchall()]
        conn.commit()
        conn.close()
        return json.dumps(items, indent=4, default=custom_serializer)
    except Exception as err:
        logger.exception(f"preview fetching error:{err}")
        return (400, {"detail": "Data cannot be fetched."})
