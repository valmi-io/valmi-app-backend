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

logger = logging.getLogger(__name__)


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user_auth_tuple = BasicAuthentication().authenticate(request)
        if user_auth_tuple is not None:
            (user, token) = user_auth_tuple
            request.user = user
            return user


class AuthBearer(HttpBearer):
    openapi_scheme: str = "bearer"

    def has_permission_for(self, user, workspace_id):
        for workspace in get_workspaces(user):
            logger.debug("checking workspace %s", workspace.id)
            if str(workspace.id) == workspace_id:
                return True
        return False

    def authenticate(self, request, token):
        user_auth_tuple = BearerAuthentication().authenticate(request)
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


api = NinjaAPI(
    version="1.0",
    csrf=False,
    title="Valmi App Backend API",
    description="App Backend API Serves the Valmi App Frontend",
    urls_namespace="public_api",
)

if config("AUTHENTICATION", default=True, cast=bool):
    api.add_router("v1/public/", public_api_router, auth=[AuthBearer()])
    api.add_router("v1/superuser/", superuser_api_router, auth=[BasicAuth()])

else:
    api.add_router("v1/public/", public_api_router)
    api.add_router("v1/superuser/", superuser_api_router)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

urlpatterns += core_urlpatterns
