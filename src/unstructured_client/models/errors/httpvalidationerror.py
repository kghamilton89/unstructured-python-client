"""Code generated by Speakeasy (https://speakeasyapi.dev). DO NOT EDIT."""

from __future__ import annotations
import dataclasses
from .validationerror import ValidationError
from dataclasses_json import Undefined, dataclass_json
from typing import List, Optional
from unstructured_client import utils


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclasses.dataclass
class HTTPValidationError(Exception):
    detail: Optional[List[ValidationError]] = dataclasses.field(
        default=None,
        metadata={
            "dataclasses_json": {
                "letter_case": utils.get_field_name("detail"),
                "exclude": lambda f: f is None,
            }
        },
    )

    def __str__(self) -> str:
        return utils.marshal_json(self)
