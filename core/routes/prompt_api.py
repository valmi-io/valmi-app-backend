import datetime
import json
import logging
from typing import List

import psycopg2
from ninja import Router
from pydantic import Json

from core.models import (Credential, Prompt, Source, SourceAccessInfo,
                         StorageCredentials, Sync)
from core.schemas.prompt import PromptPreviewSchemaIn, TableInfo
from core.schemas.schemas import (DetailSchema, PromptByIdSchema,
                                  PromptSchemaOut)
from core.services.prompts import PromptService

logger = logging.getLogger(__name__)
router = Router()


@router.get("/workspaces/{workspace_id}/prompts", response={200: List[PromptSchemaOut], 500: DetailSchema})
def get_prompts(request, workspace_id):
    try:
        prompts = list(Prompt.objects.all().values())
        connector_ids = list(Credential.objects.values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        for prompt in prompts:
            prompt["id"] = str(prompt["id"])
            prompt["enabled"] = PromptService.is_enabled(workspace_id, prompt)
        return prompts
    except Exception as err:
        logger.exception("prompts listing error:" + err)
        return (500, {"detail": "The list of prompts cannot be fetched."})


@router.get("/workspaces/{workspace_id}/prompts/{prompt_id}", response={200: PromptByIdSchema, 400: DetailSchema})
def get_prompt_by_id(request, workspace_id, prompt_id):
    try:
        logger.debug("listing prompts")
        prompt = Prompt.objects.get(id=prompt_id)
        if not PromptService.is_enabled(workspace_id, prompt):
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
        # checking wether prompt is enabled or not
        if not PromptService.is_enabled(workspace_id, prompt):
            detail_message = f"The prompt is not enabled. Please add '{prompt.type}' connector"
            return 400, {"detail": detail_message}
        source_access_info = SourceAccessInfo.objects.get(storage_credentials_id=prompt_req.schema_id)
        sync = Sync.objects.get(source_id=source_access_info.source.id)
        sync_id = sync.id
        # checking wether sync has finished or not(from shopify to DB)
        latest_sync_info = PromptService.is_sync_finished(sync_id)
        # if latest_sync_info.found == False or latest_sync_info.status == 'running':
        #     return 400, {"detail": "The sync is not finished. Please wait for the sync to finish."}
        storage_credentials = StorageCredentials.objects.get(id=prompt_req.schema_id)
        schema_name = storage_credentials.connector_config["schema"]
        table_info = TableInfo(
            tableSchema=schema_name,
            query=prompt.query
        )

        query = PromptService().build(table_info, prompt_req.time_window, prompt_req.filters)
        logger.debug(query)
        host = storage_credentials.connector_config.get('host')
        db_password = storage_credentials.connector_config.get('password')
        db_username = storage_credentials.connector_config.get('username')
        database = storage_credentials.connector_config.get('database')
        port = storage_credentials.connector_config.get('port')
        conn = psycopg2.connect(host=host, port=port, database=database,
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
