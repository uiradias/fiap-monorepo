"""Defensive JSON-schema validation against the contract files in infrastructure/contracts/."""
from __future__ import annotations

import json
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT7


class SchemaValidationError(Exception):
    """Raised when a payload does not conform to its JSON Schema."""


# jsonschema's draft-07 built-in FormatChecker does NOT validate `format: uuid`.
# Add an explicit checker so a non-UUID string in jobId/sessionId/userId/assetId is
# rejected at validation time instead of crashing the worker on UUID(value) later.
_FORMAT_CHECKER = FormatChecker()


@_FORMAT_CHECKER.checks("uuid", raises=ValueError)
def _check_uuid(instance: object) -> bool:
    if not isinstance(instance, str):
        return True  # leave non-string instances to the type keyword
    uuid.UUID(instance)
    return True


def _build_registry(contracts_dir: Path) -> Registry:
    """Register every *.schema.json sibling so $refs resolve by relative path."""
    registry = Registry()
    for schema_file in contracts_dir.glob("*.schema.json"):
        schema = json.loads(schema_file.read_text())
        # Each contract is a draft-07 schema. Register it under both its $id (if present)
        # and the relative filename so cross-file $refs like "analysis-report.schema.json"
        # resolve correctly.
        resource = DRAFT7.create_resource(schema)
        registry = registry.with_resource(uri=schema_file.name, resource=resource)
        if "$id" in schema:
            registry = registry.with_resource(uri=schema["$id"], resource=resource)
    return registry


@lru_cache(maxsize=8)
def _load_validator(schema_path_str: str, contracts_dir_str: str) -> Draft7Validator:
    schema_path = Path(schema_path_str)
    contracts_dir = Path(contracts_dir_str)
    schema = json.loads(schema_path.read_text())
    Draft7Validator.check_schema(schema)
    # FORMAT_CHECKER enforces `format: uuid` and other format keywords. Without it
    # they are informational only — a bad UUID slips through and crashes the worker
    # later on `UUID(value)`.
    return Draft7Validator(
        schema,
        registry=_build_registry(contracts_dir),
        format_checker=_FORMAT_CHECKER,
    )


def _validate(payload: Any, schema_path: Path, contracts_dir: Path) -> None:
    validator = _load_validator(str(schema_path.resolve()), str(contracts_dir.resolve()))
    try:
        validator.validate(payload)
    except ValidationError as e:
        raise SchemaValidationError(
            f"{schema_path.name}: {e.message} at {list(e.absolute_path)}"
        ) from e


def validate_analysis_job(payload: dict[str, Any], contracts_dir: Path) -> None:
    _validate(payload, contracts_dir / "analysis-jobs.schema.json", contracts_dir)


def validate_analysis_result(payload: dict[str, Any], contracts_dir: Path) -> None:
    _validate(payload, contracts_dir / "analysis-results.schema.json", contracts_dir)


def validate_analysis_report(payload: dict[str, Any], contracts_dir: Path) -> None:
    _validate(payload, contracts_dir / "analysis-report.schema.json", contracts_dir)
