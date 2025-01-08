import logging
from typing import Type

from django.urls import path

from brapi.api import BaseAPI

log = logging.getLogger(__name__)


class Router:
    def __init__(self):
        self.urlpatterns = []

    def add(self, klass: Type[BaseAPI], name=None):
        if not name:
            module_name = klass.__module__  # Get the module path, e.g. "jobs.apis"
            name = module_name.split(".")[
                0
            ]  # Extract the top-level package name, e.g. "jobs"

        base_url = f"{name}/"
        detail_url = f"{name}/<str:pk>/"

        # Register the URLs for list and detail views
        self.urlpatterns.append(path(base_url, klass.as_view(), name=f"{name}-list"))
        self.urlpatterns.append(
            path(detail_url, klass.as_view(), name=f"{name}-detail")
        )

        log.info("Adding urls [%s, %s] for package %s", base_url, detail_url, name)

    @property
    def urls(self):
        return self.urlpatterns
