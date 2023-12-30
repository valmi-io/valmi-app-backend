"""
Copyright (c) 2023 valmi.io <https://github.com/valmi-io>

Created Date: Friday, December 29th 2023, 10:53:57 am
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging

import requests
from ninja import Router
from pydantic import Json
from decouple import config
from core.api import SHORT_TIMEOUT
from core.schemas import GenericJsonSchema
from .models import ValmiUserIDJitsuApiToken

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_bearer_header(bearer_token):
    return {"Authorization": f"Bearer {bearer_token}"} if bearer_token else {}


# Object Schema Definitions
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
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.get(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/config/{type}",
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


@router.post("/workspaces/{workspace_id}/config/{type}", response={200: Json, 500: Json})
def create_obj(request, workspace_id, type, payload: GenericJsonSchema):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    response = requests.post(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/config/{type}",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
        json=payload.dict(),
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