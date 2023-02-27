from django.conf.urls import include, url

core_urlpatterns = [
    url(r"^api/v1/", include("djoser.urls")),
    url(r"^api/v1/", include("djoser.urls.authtoken")),
    url(r"^api/v1/", include("djoser.urls.jwt")),
]
