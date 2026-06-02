"""Compatibility patches for ``fastapi-mcp``.

``fastapi-mcp`` (<=0.4.0) inlines OpenAPI ``$ref`` entries with
``resolve_schema_references`` but does not track already-visited schemas.
Self-referential Pydantic models (e.g. ``TableHeader.children`` or the
``TableCell``/``TableBlock`` cycle) therefore trigger an infinite recursion
(``RecursionError``) when the MCP tools are built from the OpenAPI schema.

This module provides a cycle-aware drop-in replacement and patches the two
modules that reference the original function.
"""

from typing import Any, Dict, FrozenSet, Optional


def _resolve_schema_references_safe(
    schema_part: Dict[str, Any],
    reference_schema: Dict[str, Any],
    _seen: Optional[FrozenSet[str]] = None,
) -> Dict[str, Any]:
    """Resolve OpenAPI ``$ref`` entries while breaking reference cycles.

    Behaves like the original ``fastapi_mcp`` implementation but keeps track of
    the schema names currently being expanded along the active branch. When a
    ``$ref`` points to a model already being expanded, it is replaced by a
    generic object placeholder instead of being inlined again, which stops the
    recursion for self-referential models.
    """
    if _seen is None:
        _seen = frozenset()

    schema_part = schema_part.copy()
    branch_seen = _seen

    ref_path = schema_part.get("$ref")
    if isinstance(ref_path, str) and ref_path.startswith("#/components/schemas/"):
        model_name = ref_path.split("/")[-1]

        if model_name in _seen:
            # Cycle detected: do not inline again, leave a generic placeholder.
            schema_part.pop("$ref")
            schema_part.setdefault("type", "object")
            schema_part.setdefault("title", model_name)
            return schema_part

        schemas = reference_schema.get("components", {}).get("schemas", {})
        if model_name in schemas:
            ref_schema = schemas[model_name].copy()
            schema_part.pop("$ref")
            schema_part.update(ref_schema)
            branch_seen = _seen | {model_name}

    for key, value in schema_part.items():
        if isinstance(value, dict):
            schema_part[key] = _resolve_schema_references_safe(value, reference_schema, branch_seen)
        elif isinstance(value, list):
            schema_part[key] = [
                (_resolve_schema_references_safe(item, reference_schema, branch_seen) if isinstance(item, dict) else item) for item in value
            ]

    return schema_part


def patch_fastapi_mcp_recursion() -> None:
    """Install the cycle-aware ``resolve_schema_references`` implementation.

    Both ``fastapi_mcp.openapi.utils`` and ``fastapi_mcp.openapi.convert`` (which
    imports the function by name) are patched so the replacement is always used.
    """
    from fastapi_mcp.openapi import convert as _convert
    from fastapi_mcp.openapi import utils as _utils

    _utils.resolve_schema_references = _resolve_schema_references_safe
    _convert.resolve_schema_references = _resolve_schema_references_safe
