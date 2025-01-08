import json

from django.test import Client, TestCase
from pydantic import BaseModel

from brapi.api import APIRequest, BaseAPI
from brapi.decorators import validate


# Define Pydantic models for validation
class QueryModel(BaseModel):
    key: str


class BodyModel(BaseModel):
    value: int


class OptionalQuery(BaseModel):
    value: int = None


class TestAPIHandler(BaseAPI):
    @validate(query=QueryModel, body=BodyModel)
    def create(self, request):
        query = request.validated_query
        body = request.validated_body
        return {"query": query.dict(), "body": body.dict()}

    @validate(query=QueryModel, body=BodyModel)
    def list(self, request):
        query = request.validated_query
        return {"query": query.dict()}

    @validate(query=OptionalQuery)
    def retrieve(self, request: APIRequest, pk):
        return {"pk": pk}


class TestBaseAPI(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_handler = TestAPIHandler.as_view()

    def test_create_success(self):
        response = self.client.post(
            "/api/test/",
            data=json.dumps({"value": 42}),
            content_type="application/json",
            QUERY_STRING="key=test",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"query": {"key": "test"}, "body": {"value": 42}}
        )

    def test_create_invalid_query(self):
        response = self.client.post(
            "/api/test/",
            data=json.dumps({"value": 42}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_create_invalid_body(self):
        response = self.client.post(
            "/api/test/",
            data=json.dumps({"invalid_field": "oops"}),
            content_type="application/json",
            QUERY_STRING="key=test",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_list_success(self):
        response = self.client.get("/api/test/?key=test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"query": {"key": "test"}})

    def test_list_invalid_query(self):
        response = self.client.get("/api/test/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_retrieve(self):
        response = self.client.get("/api/test/1/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["pk"], "1")
