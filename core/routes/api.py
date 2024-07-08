"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

from core.schemas.schemas import UserSchemaOut
import logging
from typing import Any, Optional

from decouple import config
from django.conf import settings
from django.http import HttpRequest
from ninja import NinjaAPI, Router
from ninja.compatibility import get_headers
from ninja.security import HttpBasicAuth, HttpBearer
from rest_framework.authentication import BasicAuthentication

from core.routes.connector_api import router as connector_api_router
from core.routes.engine_api import router as superuser_api_router
from core.routes.explore_api import router as explore_api_router
from core.routes.oauth_api import router as oauth_api_router
from core.routes.package_api import router as package_api_router
from core.routes.prompt_api import router as prompt_api_router
from core.routes.social_auth import router as social_api_router
from core.routes.stream_api import router as stream_api_router
from core.routes.workspace_api import router as workspace_api_router
from core.routes.shopify_api import router as shopify_api_router
from valmi_app_backend.utils import BearerAuthentication

from core.models import User

# Get an instance of a logger
logger = logging.getLogger(__name__)


auth_enabled = config("AUTHENTICATION", default=True, cast=bool)


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        if auth_enabled == False:
            return True
        try:
            user_auth_tuple = BasicAuthentication().authenticate(request)
        except Exception:
            user_auth_tuple = None
        if user_auth_tuple is not None:
            (user, token) = user_auth_tuple
            request.user = user
            # Basic Auth allowed only for superuser.
            if user.is_superuser:
                return user
            return None
        return None


class AuthBearer(HttpBearer):
    openapi_scheme: str = "bearer"

    def __call__(self, request: HttpRequest) -> Optional[Any]:
        return self.authenticate(request)

    def has_permission_for(self, user, workspace_id):
        if auth_enabled == False:
            return True
        for workspace in get_workspaces(user):
            logger.debug("checking workspace %s", workspace.id)
            if str(workspace.id) == workspace_id:
                return True
        return False

    def authenticate(self, request):
        '''
        logger.debug("enabled " +config('PUBLIC_SYNC_ENABLED'))
        logger.debug("pub " +config('PUBLIC_WORKSPACE'))
        logger.debug("sync " +config('PUBLIC_SYNC'))
        logger.debug("authtoken " +config('PUBLIC_AUTH_TOKEN'))
        logger.debug("path "+  request.path)
        logger.debug("hardcoded "+  f'/api/v1/workspaces/{config("PUBLIC_WORKSPACE")}/syncs/{config("PUBLIC_SYNC")}/runs/')
        '''
        if (config('PUBLIC_SYNC_ENABLED', default=False) and
                request.path == f'/api/v1/workspaces/{config("PUBLIC_WORKSPACE")}/syncs/{config("PUBLIC_SYNC")}/runs/'):
            return config('PUBLIC_AUTH_TOKEN')

        headers = get_headers(request)
        auth_value = headers.get(self.header)
        if not auth_value:
            return None
        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            if settings.DEBUG:
                logger.error(f"Unexpected auth - '{auth_value}'")
            return None
        token = " ".join(parts[1:])

        try:
            user_auth_tuple = BearerAuthentication().authenticate(request)
        except Exception:
            user_auth_tuple = None
        if user_auth_tuple is not None:
            (user, token) = user_auth_tuple  # here come your user object
            request.user = user
            # get Workspace Id.
            arr = request.get_full_path().split("/")
            for i, el in enumerate(arr):
                if el == "workspaces" and len(arr) > i + 1:
                    workspace_id = arr[i + 1]
                    logger.debug(workspace_id)
                    if not self.has_permission_for(user, workspace_id):
                        return None
                    break
            return token
        return None


def get_workspaces(user):
    queryset = User.objects.prefetch_related("organizations").get(id=user.id)
    for organization in queryset.organizations.all():
        for workspace in organization.workspaces.all():
            yield workspace


router = Router()


@router.get("/spaces/", response=UserSchemaOut)
def list_spaces(request):
    user_id = request.user.id
    queryset = User.objects.prefetch_related("organizations").get(id=user_id)
    logger.debug(queryset)
    return queryset


api = NinjaAPI(
    version="1.0",
    csrf=False,
    title="Valmi App Backend API",
    description="App Backend API Serves the Valmi App Frontend",
    urls_namespace="public_api",
)

api.add_router("/v1/auth/social", social_api_router)

api.add_router("v1/", router, auth=[AuthBearer(), BasicAuth()])
router.add_router("superuser/", superuser_api_router, auth=[BasicAuth()])
router.add_router("streams/", stream_api_router, tags=["streams"])
router.add_router("oauth/", oauth_api_router, tags=["oauth"])

router.add_router("packages", package_api_router, tags=["packages"])
router.add_router("", workspace_api_router, tags=["workspaces"])
router.add_router("", prompt_api_router, tags=["prompts"])
router.add_router("", explore_api_router, tags=["explores"])
router.add_router("", connector_api_router, tags=["connectors"])
router.add_router("", shopify_api_router, tags=["shopify"])
