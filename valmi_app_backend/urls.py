from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from core.api import router as valmi_app_backend_router
from core.urls import core_urlpatterns

api = NinjaAPI(
    version="1.0",
    csrf=True,
    title="Title API project",
    description="Description API project",
    urls_namespace="public_api",
)

api.add_router("/valmi/", valmi_app_backend_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

urlpatterns += core_urlpatterns
