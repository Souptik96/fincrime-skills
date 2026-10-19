"""A dependency-free JSON Schema validator.

ADR-0002 forbids runtime dependencies in ``fincrime-core``, so the standard
library has no JSON Schema validator. This module implements the subset of
JSON Schema 2020-12 that the Finding Contract uses:

``type``, ``enum``, ``const``, ``properties``, ``required``,
``additionalProperties``, ``items``, ``prefixItems``, ``minItems``,
``maxItems``, ``uniqueItems``, ``minLength``, ``maxLength``, ``pattern``,
``minimum``, ``maximum``, ``exclusiveMinimum``, ``exclusiveMaximum``,
``multipleOf``, ``allOf``, ``anyOf``, ``oneOf``, ``not``, ``if``/``then``/
``else``, ``format`` (annotation, with ``date-time`` checked), ``$ref`` to
``$defs``/``#/$defs/...``, ``$defs``, ``patternProperties``, and
``propertyNames``.

The schemas themselves remain **standards-compliant**: any third-party JSON
Schema validator enforces the same rules. This implementation exists so the
core can be installed and run in an air-gapped environment with no index
access. A contract test asserts that this validator and the reference
implementation agree on the corpus.

Every error is returned as a :class:`SchemaError`; the validator never raises
on a bad instance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping, Sequence

__all__ = ["SchemaError", "JsonSchemaValidator", "FORMAT_CHECKERS"]

#: ``format`` is an annotation in JSON Schema, but ``date-time`` is checked
#: anyway because a malformed timestamp in provenance is a real defect.
FORMAT_CHECKERS = {
    "date-time": lambda value: _is_date_time(value),
    "date": lambda value: _is_date(value),
}


def _is_date_time(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class SchemaError:
    """A single validation failure."""

    path: str
    message: str
    keyword: str

    def __str__(self) -> str:
        location = self.path or "$"
        return f"{location}: {self.message}"


_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list, tuple),
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "null": (type(None),),
}


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    types = _TYPE_MAP.get(expected)
    if types is None:
        return True
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, (list, tuple))
    return isinstance(value, types) and not (
        expected == "string" and isinstance(value, bool)
    )


class JsonSchemaValidator:
    """Validates instances against a JSON Schema document."""

    __slots__ = ("_root",)

    def __init__(self, schema: Mapping[str, Any]) -> None:
        self._root = schema

    def validate(self, instance: Any) -> list[SchemaError]:
        """Validate ``instance``, returning every error found (never raising)."""
        errors: list[SchemaError] = []
        self._validate(instance, self._root, "$", errors)
        return errors

    def is_valid(self, instance: Any) -> bool:
        return not self.validate(instance)

    # -- internals ------------------------------------------------------

    def _resolve_ref(self, ref: str) -> Mapping[str, Any] | None:
        if not ref.startswith("#"):
            return None
        pointer = ref[1:]
        if pointer in ("", "/"):
            return self._root
        if not pointer.startswith("/"):
            return None
        current: Any = self._root
        for raw_token in pointer.split("/")[1:]:
            token = raw_token.replace("~1", "/").replace("~0", "~")
            if isinstance(current, Mapping) and token in current:
                current = current[token]
            elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                current = current[int(token)]
            else:
                return None
        return current if isinstance(current, Mapping) else None

    def _validate(
        self,
        instance: Any,
        schema: Mapping[str, Any] | bool,
        path: str,
        errors: list[SchemaError],
    ) -> None:
        if schema is True or schema == {}:
            return
        if schema is False:
            errors.append(SchemaError(path=path, message="schema forbids any value here", keyword="false"))
            return
        if not isinstance(schema, Mapping):
            return

        if "$ref" in schema:
            target = self._resolve_ref(schema["$ref"])
            if target is None:
                errors.append(
                    SchemaError(path=path, message=f"unresolvable $ref {schema['$ref']!r}", keyword="$ref")
                )
                return
            self._validate(instance, target, path, errors)
            # 2020-12 allows sibling keywords alongside $ref; keep evaluating them.

        if "type" in schema:
            expected = schema["type"]
            options = expected if isinstance(expected, list) else [expected]
            if not any(_type_matches(instance, option) for option in options):
                errors.append(
                    SchemaError(
                        path=path,
                        message=f"expected type {'/'.join(options)}, got {type(instance).__name__}",
                        keyword="type",
                    )
                )
                return

        if "const" in schema and not _json_equal(instance, schema["const"]):
            errors.append(
                SchemaError(path=path, message=f"expected constant {schema['const']!r}", keyword="const")
            )

        if "enum" in schema and not any(_json_equal(instance, option) for option in schema["enum"]):
            errors.append(
                SchemaError(path=path, message=f"value {instance!r} is not one of the permitted values", keyword="enum")
            )

        for keyword, combiner in (("allOf", all), ("anyOf", any), ("oneOf", None)):
            if keyword not in schema:
                continue
            results = []
            for index, sub in enumerate(schema[keyword]):
                sub_errors: list[SchemaError] = []
                self._validate(instance, sub, path, sub_errors)
                results.append(sub_errors)
            if keyword == "allOf":
                for sub_errors in results:
                    errors.extend(sub_errors)
            elif keyword == "anyOf":
                if all(sub_errors for sub_errors in results):
                    errors.append(
                        SchemaError(path=path, message="value does not match any of the anyOf alternatives", keyword=keyword)
                    )
            else:
                matched = sum(1 for sub_errors in results if not sub_errors)
                if matched != 1:
                    errors.append(
                        SchemaError(
                            path=path,
                            message=f"value matched {matched} oneOf alternatives, expected exactly 1",
                            keyword=keyword,
                        )
                    )

        if "not" in schema:
            sub_errors: list[SchemaError] = []
            self._validate(instance, schema["not"], path, sub_errors)
            if not sub_errors:
                errors.append(SchemaError(path=path, message="value must not match the 'not' schema", keyword="not"))

        if "if" in schema:
            condition_errors: list[SchemaError] = []
            self._validate(instance, schema["if"], path, condition_errors)
            branch = "then" if not condition_errors else "else"
            if branch in schema:
                self._validate(instance, schema[branch], path, errors)

        if isinstance(instance, dict):
            self._validate_object(instance, schema, path, errors)
        elif isinstance(instance, (list, tuple)):
            self._validate_array(instance, schema, path, errors)
        elif isinstance(instance, str):
            self._validate_string(instance, schema, path, errors)
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            self._validate_number(instance, schema, path, errors)

        if "format" in schema:
            checker = FORMAT_CHECKERS.get(schema["format"])
            if checker is not None and not checker(instance):
                errors.append(
                    SchemaError(
                        path=path,
                        message=f"value {instance!r} is not a valid {schema['format']}",
                        keyword="format",
                    )
                )

    def _validate_object(
        self,
        instance: Mapping[str, Any],
        schema: Mapping[str, Any],
        path: str,
        errors: list[SchemaError],
    ) -> None:
        for name in schema.get("required", ()):
            if name not in instance:
                errors.append(
                    SchemaError(path=path, message=f"missing required property {name!r}", keyword="required")
                )

        properties = schema.get("properties", {})
        pattern_properties = schema.get("patternProperties", {})
        additional = schema.get("additionalProperties", True)

        for key, value in instance.items():
            child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
            handled = False

            if key in properties:
                self._validate(value, properties[key], child_path, errors)
                handled = True

            for pattern, sub_schema in pattern_properties.items():
                if re.search(pattern, key):
                    self._validate(value, sub_schema, child_path, errors)
                    handled = True

            if not handled and additional is not True:
                if additional is False:
                    errors.append(
                        SchemaError(
                            path=child_path,
                            message=f"additional property {key!r} is not permitted",
                            keyword="additionalProperties",
                        )
                    )
                else:
                    self._validate(value, additional, child_path, errors)

            if "propertyNames" in schema:
                name_errors: list[SchemaError] = []
                self._validate(key, schema["propertyNames"], child_path, name_errors)
                errors.extend(name_errors)

        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"object has {len(instance)} properties, minimum is {schema['minProperties']}",
                    keyword="minProperties",
                )
            )
        if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"object has {len(instance)} properties, maximum is {schema['maxProperties']}",
                    keyword="maxProperties",
                )
            )

    def _validate_array(
        self,
        instance: Sequence[Any],
        schema: Mapping[str, Any],
        path: str,
        errors: list[SchemaError],
    ) -> None:
        prefix = schema.get("prefixItems", [])
        for index, sub_schema in enumerate(prefix):
            if index < len(instance):
                self._validate(instance[index], sub_schema, f"{path}[{index}]", errors)

        if "items" in schema:
            for index in range(len(prefix), len(instance)):
                self._validate(instance[index], schema["items"], f"{path}[{index}]", errors)

        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"array has {len(instance)} items, minimum is {schema['minItems']}",
                    keyword="minItems",
                )
            )
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"array has {len(instance)} items, maximum is {schema['maxItems']}",
                    keyword="maxItems",
                )
            )
        if schema.get("uniqueItems") is True:
            seen: list[Any] = []
            for item in instance:
                if any(_json_equal(item, other) for other in seen):
                    errors.append(
                        SchemaError(path=path, message="array items are not unique", keyword="uniqueItems")
                    )
                    break
                seen.append(item)

    def _validate_string(
        self, instance: str, schema: Mapping[str, Any], path: str, errors: list[SchemaError]
    ) -> None:
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"string length {len(instance)} is below minimum {schema['minLength']}",
                    keyword="minLength",
                )
            )
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"string length {len(instance)} exceeds maximum {schema['maxLength']}",
                    keyword="maxLength",
                )
            )
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"string does not match pattern {schema['pattern']!r}",
                    keyword="pattern",
                )
            )

    def _validate_number(
        self, instance: float, schema: Mapping[str, Any], path: str, errors: list[SchemaError]
    ) -> None:
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(
                SchemaError(path=path, message=f"value {instance} is below minimum {schema['minimum']}", keyword="minimum")
            )
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(
                SchemaError(path=path, message=f"value {instance} exceeds maximum {schema['maximum']}", keyword="maximum")
            )
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"value {instance} is not greater than {schema['exclusiveMinimum']}",
                    keyword="exclusiveMinimum",
                )
            )
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            errors.append(
                SchemaError(
                    path=path,
                    message=f"value {instance} is not less than {schema['exclusiveMaximum']}",
                    keyword="exclusiveMaximum",
                )
            )
        if "multipleOf" in schema:
            divisor = schema["multipleOf"]
            if divisor and (instance % divisor) != 0:
                errors.append(
                    SchemaError(
                        path=path,
                        message=f"value {instance} is not a multiple of {divisor}",
                        keyword="multipleOf",
                    )
                )


def _json_equal(left: Any, right: Any) -> bool:
    """JSON equality: booleans are not numbers, ints and floats compare by value."""
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            return False
        return all(_json_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return False
        return all(_json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return float(left) == float(right)
    return left == right
