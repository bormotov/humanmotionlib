# SPDX-License-Identifier: Apache-2.0
"""Closed source contracts with offline schema references and finite numbers."""

import json
import math
from pathlib import Path

import yaml

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from humanmotionlib.package_resources import read_text


SCHEMA_NAMES = {"profile", "mobility", "body-groups", "humanoid-map", "diagnostic", "review-scene"}


from humanmotionlib.finite import SourceValidationError, require_finite


class UniqueKeyLoader(getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in result
            except TypeError as error:
                raise SourceValidationError(f"Unhashable YAML key at line {key_node.start_mark.line+1}") from error
            if duplicate:
                raise SourceValidationError(f"Duplicate YAML key {key!r} at line {key_node.start_mark.line+1}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_yaml(path):
    try:
        return yaml.load(Path(path).read_text(), Loader=UniqueKeyLoader)
    except (yaml.YAMLError, SourceValidationError) as error:
        raise SourceValidationError(f"{path}: {error}") from error



def schema_validator(name, root=None):
    if name not in SCHEMA_NAMES:
        raise SourceValidationError(f"Unknown source contract: {name}")
    schemas = {}
    if root is None:
        from humanmotionlib.package_resources import runtime_manifest
        schema_names = sorted(name for name in runtime_manifest()["resources"]
                              if name.startswith("schema/") and name.endswith(".schema.json"))
        schema_text = {name: read_text(name) for name in schema_names}
    else:
        schema_dir = Path(root) / "schema"
        schema_text = {path.relative_to(root).as_posix(): path.read_text()
                       for path in sorted(schema_dir.glob("*.schema.json"))}
    for text in schema_text.values():
        schema = json.loads(text)
        Draft202012Validator.check_schema(schema)
        schemas[schema["$id"]] = schema
    registry = Registry().with_resources(
        (uri, Resource.from_contents(schema)) for uri, schema in schemas.items())
    schema = json.loads(schema_text[f"schema/{name}.schema.json"])
    return Draft202012Validator(schema, registry=registry)


def validate_document(document, name, root=None):
    identifier = document.get("id", "source") if isinstance(document, dict) else "source"
    require_finite(document, identifier=identifier)
    errors = sorted(schema_validator(name, root).iter_errors(document),
                    key=lambda error: str(list(error.absolute_path)))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        raise SourceValidationError(f"{identifier} {path}: {error.message}")
    return document
