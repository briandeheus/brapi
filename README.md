# Brapi (Brian's API)

Welcome to **Brapi** — showing you how REST APIs should really be done. This is not intended to be a replacement for
DRF, but it does solve some of my gripes with it.

## Warning

This shit is so experimental, only a fool would use this in production.

## Introduction

**Brapi** is a minimalistic API framework that makes sure you’re doing REST the way it's intended. The biggest
issue I see, is people using actions in REST, defeating the purpose of REST, which is transferring state.

## The Rules

There are a few guiding principles with **Brapi**:

- **I explicitly do not support actions**. Every action can be represented as a state transfer. Want to log out? Delete
  the session. Want turn off a server? Change the server's state.

- **Authentication is left up to you,** because I have no idea how you want to do authentication. JWT? Bearer Tokens?
  Brapi has one method called `authenticate` that you can overwrite. Go nuts, brothers and sisters.

- **Validation**? We do some basic authentication and use Pydantic, additionally we also have sane error catching.
  Nobody wants to see the ugly Django stack trace you forgot to turn off in production.

## Getting Started

**Define your request and query models using Pydantic.**

Yes, Pydantic, because it's good enough. Define a model, validate it, and make sure your API doesn’t become a wild mess.

```python
from pydantic import BaseModel


class CreateFilingBody(BaseModel):
    accession_number: str


class RetrieveFilingQuery(BaseModel):
    cik: int = None
```

**Create an API** by inheriting `BaseAPI`. Remember, this is where you enforce your REST state transfers.

```python
from pydantic_models import CreateFilingBody, RetrieveFilingQuery
from brapi.decorators import validate
from brapi.api import BaseAPI, APIRequest


class API(BaseAPI):

    @validate(body=CreateFilingBody)
    def create(self, request: APIRequest[None, CreateFilingBody]):
        filing = Filing.objects.get(accession_number=request.validated_body.accession_number)
        return filing.to_dict()

    @validate(query=RetrieveFilingQuery)
    def list(self, request: APIRequest[RetrieveFilingQuery, None], pk):
        filings = Filing.objects.filter(cik=request.validated_query.cik)
        return [f.to_dict() for f in filings]
```

**Create a new router** and register it. Names are implied.

```python
from brapi.router import Router
import filings.apis

v1_router = Router()
v1_router.add(filings.apis.API)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(v1_router.urls)),
]
```

## Some Examples

Here’s what using **Brapi** should look like:

- **Logging out?**
    - Bad: `POST /brapi/v1/account/logout`
    - Good: `DELETE /brapi/v1/sessions/$sessionId/`

- **Reprocessing a job?**
    - Bad: `POST /brapi/v1/jobs/$jobId/process/`
    - Good: `PUT /brapi/v1/jobs/$jobId`
    - Request body: `{"status": "pending"}`

- **Turning off a server?**
    - Bad: `POST /brapi/v1/servers/$serverId/shutdown/`
    - Good: `PUT /brapi/v1/servers/$serverId`
    - Request body: `{"power_state": "off"}`

If you see yourself reaching for a `POST /some/action`, think again. **Brapi** isn’t here to do things for you. It’s
here to make you do things _right_.

## Error Handling

When things go wrong, we try to handle it as gracefully as possible.

- **Validation errors** Handled gracefully. Thrown by Pydantic.
- **Missing objects** We fetch `ObjectNotFound` and return a 404.
- **Unimplemented methods** Yeah, we let you know. Expect a `400` with `"method_not_supported"` because we're not
  pretending something works when it doesn’t.
- **Your own screw-ups?** Raise an `APIException`, or we'll return a `500` with `"server_borked"` for you.

## Why Use Brapi?

DRF does a lot, and it's too opinionated about how it does it. Serializers are a mess, and having `@actions` is the
biggest sin of all. Brapi frees you from all of that, giving you more freedom, whilst making sure that you're as RESTful
as possible.

