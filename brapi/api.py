import json
import logging
import traceback
from typing import Generic, TypeVar

from django.db import models
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError

from brapi.exceptions import APIException

log = logging.getLogger(__name__)

B = TypeVar("B")
Q = TypeVar("Q")


class APIRequest(HttpRequest, Generic[Q, B]):
    validated_query: Q
    validated_body: B


class BaseAPI(View):
    """
    We explicitly do not support actions.
    An action should be able to be represented as a state transfer.

    Logging out?
    Bad:
    POST /brapi/v1/account/logout
    Good:
    DELETE /brapi/v1/sessions/$sessionId/

    Reprocessing a job?
    Bad:
    POST /brapi/v1/jobs/$jobId/process/
    Good:
    PUT /brapi/v1/jobs/$jobId
    {"status": "pending"}

    Turning off a server?
    Bad:
    POST /brapi/v1/servers/$serverId/shutdown/
    Good:
    PUT /brapi/v1/servers/$serverId
    {"power_state": "off"}

    Running a Linux command?
    Bad:
    POST /brapi/v1/servers/$serverId/run/
    {"cmd": ["rm", "-rf", "/"]}
    Good:
    POST /brapi/v1/commands
    {"server_id": $serverId, "cmd": ["rm", "-rf", "/"]}
    """

    def _validate(self, function, request):

        query_model = None
        body_model = None
        validated_query = None
        validated_body = None

        if hasattr(function, "validate_query"):
            query_model = function.validate_query
        if hasattr(function, "validate_body"):
            body_model = function.validate_body

        if query_model:
            query_data = request.GET.dict()
            validated_query = query_model(**query_data)

        if body_model:
            if request.method in ("POST", "PUT", "PATCH"):
                if request.content_type == "application/json":
                    body_data = json.loads(request.body.decode("utf-8"))
                else:
                    body_data = request.POST.dict()

                validated_body = body_model(**body_data)

        else:
            validated_body = None

        setattr(request, "validated_body", validated_body)
        setattr(request, "validated_query", validated_query)

    def create(self, request: APIRequest):
        """
        Used to create an item.
        :param request:
        :return:
        """
        raise NotImplementedError

    def list(self, request: APIRequest):
        """
        Used for listing items.
        :param request:
        :return:
        """
        raise NotImplementedError

    def retrieve(self, request: APIRequest, pk):
        """
        Used to retrieve an item
        :param request:
        :param pk:
        :return:
        """
        raise NotImplementedError

    def update(self, request: APIRequest, pk):
        """
        Used when updating items.
        :param request:
        :param pk:
        :return:
        """
        raise NotImplementedError

    def destroy(self, request: APIRequest, pk):
        """
        Used for deleting items.
        :param request:
        :param pk:
        :return:
        """
        raise NotImplementedError

    def authenticate(self, request: APIRequest):
        """
        Gets called before every request. Because I don't want to tell you how to do auth,
        all calls are authless by default. Override this method in the base class, or subclasses.
        I really don't care.
        :param request:
        :return:
        """
        pass

    def validate(self, request: APIRequest):
        """
        Again, gets called after authentication. Use this, or not.
        :param request:
        :return:
        """
        pass

    # HTTP Method Handlers

    def get(self, request, *args, **kwargs):
        self._validate(self.retrieve, request)
        if pk := kwargs.get("pk"):
            return self.retrieve(request, pk)
        return self.list(request)

    def post(self, request):
        self._validate(self.create, request)
        return self.create(request)

    def put(self, request, **kwargs):

        if pk := kwargs.get("pk"):
            self._validate(self.put, request)
            return self.update(request, pk)

        return JsonResponse({"error": "PUT method requires 'pk' parameter"}, status=400)

    def delete(self, request, **kwargs):

        if pk := kwargs.get("pk"):
            self._validate(self.put, request)
            return self.destroy(request, pk)

        return JsonResponse(
            {"error": "DELETE method requires 'pk' parameter"}, status=400
        )

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        log.info("Incoming request method=%s path=%s", request.method, request.path)

        self.authenticate(request)
        self.validate(request)

        response = None

        try:
            response = super().dispatch(request, *args, **kwargs)
            if type(response) is tuple:
                response, code = response
                return JsonResponse(response, status=code)
            return JsonResponse(response)

        except ValidationError as e:
            log.warning(
                "Invalid request method=%s path=%s exception=%s",
                request.method,
                request.path,
                e,
            )
            return JsonResponse({"error": e.errors()}, status=400)

        except json.JSONDecodeError:
            log.warning(
                "Invalid request body method=%s path=%s",
                request.method,
                request.path,
            )
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        except NotImplementedError:
            return JsonResponse(
                {"error": "Method not supported", "code": "method_not_supported"},
                status=400,
            )

        except models.ObjectDoesNotExist:
            return JsonResponse(
                {"error": "Object does not exist", "code": "not_found"}, status=404
            )

        except APIException as e:
            return JsonResponse(
                {"error": e.message, "code": e.code}, status=e.status_code
            )

        except TypeError as e:
            log.error("Return data %s invalid %s", response, e)
            return JsonResponse(
                {"error": "Server returned invalid data.", "code": "server_borked"},
                status=500,
            )

        # The final exception.
        except Exception as e:
            log.error("API call failed: %s\n%s", e, traceback.format_exc())
            return JsonResponse(
                {"error": "Unknown Error", "code": "server_borked"}, status=500
            )
