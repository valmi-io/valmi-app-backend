"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Friday, December 29th 2023, 10:53:57 am
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging
from uuid import UUID

import requests
from ninja import Router
from pydantic import Json
from decouple import config
from core.schemas.schemas import GenericJsonSchema
from core.models import ValmiUserIDJitsuApiToken
from typing import Optional

import requests
from decouple import config
from ninja import Router
from pydantic import Json

from core.routes.api_config import SHORT_TIMEOUT

from ..models import ValmiUserIDJitsuApiToken

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_bearer_header(bearer_token):
    return {"Authorization": f"Bearer {bearer_token}"}


# Object Schema Definitions
@router.get("/workspaces/{workspace_id}/api/schema/link/{type}", response={200: Json, 500: Json})
def destination_schema_obj(request, workspace_id, type):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.get(
        f"{config('STREAM_API_URL')}/api/schema/link/{type}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.get("/workspaces/{workspace_id}/api/schema/destination/{type}", response={200: Json, 500: Json})
def destination_schema_obj(request, workspace_id, type):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.get(
        f"{config('STREAM_API_URL')}/api/schema/destination/{type}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.get("/workspaces/{workspace_id}/api/schema/{type}", response={200: Json, 500: Json})
def schema_obj(request, workspace_id, type):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.get(
        f"{config('STREAM_API_URL')}/api/schema/{type}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


# CRUD for objects
@router.get("/workspaces/{workspace_id}/config/{type}", response={200: Json, 500: Json})
def get_objs(request, workspace_id, type):
    auth_key = ValmiUserIDJitsuApiToken.objects.get(workspace_id=workspace_id).api_token
    url = f"http://host.docker.internal:3000/api/{workspace_id}/config/{type}"
    response = requests.get(
        url,
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(auth_key),
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.post("/workspaces/{workspace_id}/config/{type}", response={200: Json, 500: Json})
def create_obj(request, workspace_id, type, payload: GenericJsonSchema):
    if isinstance(payload, dict):
        data = payload
    else:
        data = payload.dict()
    for key, value in data.items():
        if isinstance(value, UUID):
            data[key] = str(value)

    auth_key = ValmiUserIDJitsuApiToken.objects.get(workspace_id=workspace_id).api_token
    logger.debug(auth_key)
    auth_key_with_bearer = get_bearer_header(auth_key)
    url = f"http://host.docker.internal:3000/api/{workspace_id}/config/{type}"
    logger.debug(url)
    response = requests.post(
        url,
        timeout=SHORT_TIMEOUT,
        headers=auth_key_with_bearer,
        json=data,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.put("/workspaces/{workspace_id}/config/{type}/{id}", response={200: Json, 500: Json})
def update_obj(request, workspace_id, type, id, payload: GenericJsonSchema):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.put(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/config/{type}/{id}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
        data=json.dumps(payload.dict()),
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.delete("/workspaces/{workspace_id}/config/{type}/{id}", response={200: Json, 500: Json})
def delete_obj(request, workspace_id, type, id):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.delete(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/config/{type}/{id}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.delete("/workspaces/{workspace_id}/config/{type}", response={200: Json, 500: Json})
def delete_link_obj(request, workspace_id, type, fromId, toId):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.delete(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/config/{type}"
        f"?workspaceId={workspace_id}&fromId={fromId}&toId={toId}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


@router.get("/workspaces/{workspace_id}/events/{type}/{id}/logs", response={200: Json, 500: Json})
def get_logs(
        request, workspace_id, type, id, start: Optional[str] = "",
        end: Optional[str] = "", beforeId: Optional[str] = "", limit: Optional[int] = 25):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.get(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/log/{type}/{id}"
        f"?start={start}&end={end}&beforeId={beforeId}&limit={limit}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            return (500, response.text)
        except Exception as e:
            raise e

    return response.text


'''
def update_store():
    //hit this api
    http://localhost:3100/api/admin/fast-store-refresh
'''
