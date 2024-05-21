"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import logging

from django.contrib import admin
from django.urls import path

from core.routes.api import api
from core.urls import core_urlpatterns

logger = logging.getLogger(__name__)



urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

urlpatterns += core_urlpatterns
