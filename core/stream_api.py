"""
Copyright (c) 2023 valmi.io <https://github.com/valmi-io>

Created Date: Friday, December 29th 2023, 10:53:57 am
Author: Rajashekar Varkala @ valmi.io

"""

import logging

import requests
from ninja import Router
from pydantic import Json
from decouple import config
from core.api import SHORT_TIMEOUT
from .models import ValmiUserIDJitsuApiToken

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_bearer_header(bearer_token):
    return {"Authorization": f"Bearer {bearer_token}"} if bearer_token else {}


@router.get("/{workspace_id}/config/stream", response=Json)
def get_streams(request, workspace_id):
    authObject = ValmiUserIDJitsuApiToken.objects.get(user=request.user)
    logger.debug("get_streams %s", get_bearer_header(authObject.api_token))
    return requests.get(
        f"{config('STREAM_API_URL')}/api/{workspace_id}/config/stream",
        timeout=SHORT_TIMEOUT,
        headers=get_bearer_header(authObject.api_token),
    ).text
