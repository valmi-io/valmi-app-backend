"""
Copyright (c) 2023 valmi.io <https://github.com/valmi-io>

Created Date: Tuesday, January 23rd 2024, 3:21:31 pm
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging
import uuid


from typing import List

from ninja import Router
from pydantic import Json

from .models import Connector, Workspace, OAuthApiKeys

from core.schemas import (
    DetailSchema,
    OAuthSchema,
    OAuthSchemaIn,
    OAuthSchemaUpdateIn
)

from os.path import dirname, join


router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


# object schema
@router.get("/schema/{connector_type}", response={200: Json, 400: DetailSchema})
def get_config(request, connector_type: str):
    try:
        connector = Connector.objects.get(type=connector_type)

        if connector:
            json_file_path = join(dirname(__file__), 'oauth_schema.json')

            with open(json_file_path, 'r') as json_file:
                oauth_configs = json.load(json_file)

            # Assuming the JSON file has a "schema" key containing a dictionary of schema
            schema = oauth_configs.get('schema', {})
            # Find the configuration based on the connector_type parameter
            matching_config = schema.get(connector_type)

            if matching_config:
                return json.dumps(matching_config)

    except Exception:
        return (400, {"detail": "Configuration not found"})


# CRUD operations
@router.post("/workspaces/{workspace_id}/config/create", response={200: OAuthSchema, 400: DetailSchema})
def create_obj(request, workspace_id, payload: OAuthSchemaIn):
    data = payload.dict()
    logger.debug("payload", payload)
    try:

        workspace = Workspace.objects.get(id=workspace_id)

        logger.debug("workspace", workspace.id)

        data["id"] = uuid.uuid4()
        data["workspace"] = workspace

        result = OAuthApiKeys.objects.create(**data)

        return result
    except Exception:
        return {"detail": "The specific oauth key cannot be created."}


@router.put("/workspaces/{workspace_id}/config/update", response={200: OAuthSchema, 404: Json, 400: DetailSchema})
def update_obj(request, workspace_id, payload: OAuthSchemaUpdateIn):
    data = payload.dict()

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        oauth_key = OAuthApiKeys.objects.filter(workspace=workspace, type=data.pop("type"))

        if oauth_key.exists():

            data["workspace"] = workspace

            oauth_key.update(**data)
            return oauth_key.first()
        else:
            response_data = {"detail": "The specific oauth key cannot be updated."}
            response_json = json.dumps(response_data)

            return (404, response_json)

    except Exception:
        return {"detail": "The specific oauth key cannot be updated."}


@router.get("/workspaces/{workspace_id}/keys/{type}", response={200: List[OAuthSchema], 400: DetailSchema})
def get_obj(request, workspace_id, type):
    try:
        workspace = Workspace.objects.get(id=workspace_id)

        queryset: OAuthSchema = OAuthApiKeys.objects.filter(workspace=workspace, type=type)

        if queryset.exists():
            return [queryset.first()]
        else:
            logger.debug("No found")
            return []

    except Exception:
        return {"detail": "The specific oauth key cannot be fetched."}
