from django.contrib import admin
from django.urls import include, path

from config.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("accounts.urls")),
]
