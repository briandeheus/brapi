import logging
from typing import Type

from pydantic import BaseModel

log = logging.getLogger(__name__)


def validate(query: Type[BaseModel] = None, body: Type[BaseModel] = None):
    def decorator(view_func):
        if query:
            setattr(view_func, "validate_query", query)
        if body:
            setattr(view_func, "validate_body", body)
        return view_func

    return decorator
