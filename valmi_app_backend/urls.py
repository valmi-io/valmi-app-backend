from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from ninja.security import HttpBearer
from rest_framework.authentication import TokenAuthentication

from core.api import router as valmi_app_backend_router
from core.urls import core_urlpatterns


class AuthBearer(HttpBearer):
    openapi_scheme: str = "token"

    def authenticate(self, request, token):
        user_auth_tuple = TokenAuthentication().authenticate(request)
        if user_auth_tuple is not None:
            (user, token) = user_auth_tuple  # here come your user object
            request.user = user
            return token


api = NinjaAPI(
    version="1.0",
    csrf=True,
    title="Title API project",
    description="Description API project",
    urls_namespace="public_api",
)
api.add_router("v1/", valmi_app_backend_router, auth=AuthBearer())


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

urlpatterns += core_urlpatterns
