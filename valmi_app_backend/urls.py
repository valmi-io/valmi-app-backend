"""
Copyright (c) 2023 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import logging

from decouple import config
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from ninja.security import HttpBearer
from ninja.security import HttpBasicAuth

from core.api import router as public_api_router
from core.api import get_workspaces
from core.engine_api import router as superuser_api_router

from core.urls import core_urlpatterns
from valmi_app_backend.utils import BearerAuthentication

from rest_framework.authentication import BasicAuthentication
from ninja.compatibility import get_headers
from django.conf import settings
from django.http import HttpRequest
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        try:
            user_auth_tuple = BasicAuthentication().authenticate(request)
        except Exception:
            user_auth_tuple = None
        if user_auth_tuple is not None:
            (user, token) = user_auth_tuple
            request.user = user
            return user
        return None


class AuthBearer(HttpBearer):
    openapi_scheme: str = "bearer"

    def __call__(self, request: HttpRequest) -> Optional[Any]:
        return self.authenticate(request)
    
    def has_permission_for(self, user, workspace_id):
        for workspace in get_workspaces(user):
            logger.debug("checking workspace %s", workspace.id)
            if str(workspace.id) == workspace_id:
                return True
        return False

    def authenticate(self, request):
        if (config('PUBLIC_SYNC_ENABLED', default=False) and 
            request.get_full_path() == f'/spaces/{config("PUBLIC_WORKSPACE")}/syncs/{config("PUBLIC_SYNC")}/runs'):
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


api = NinjaAPI(
    version="1.0",
    csrf=False,
    title="Valmi App Backend API",
    description="App Backend API Serves the Valmi App Frontend",
    urls_namespace="public_api",
)

if config("AUTHENTICATION", default=True, cast=bool):
    api.add_router("v1/superuser/", superuser_api_router, auth=[BasicAuth()])
    api.add_router("v1/", public_api_router, auth=[AuthBearer()])

else:
    api.add_router("v1/superuser/", superuser_api_router)
    api.add_router("v1/", public_api_router)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

urlpatterns += core_urlpatterns
