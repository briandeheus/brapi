from django.urls import include, path

from brapi.router import Router
from brapi.tests.test_api import TestAPIHandler

router = Router()
router.add(TestAPIHandler, name="test")

urlpatterns = [
    path("api/", include(router.urls)),
]
