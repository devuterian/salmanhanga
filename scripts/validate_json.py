#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def schema_registry() -> Registry:
    registry = Registry()
    for path in SCHEMAS.glob("*.json"):
        contents = load(path)
        registry = registry.with_resource(contents["$id"], Resource.from_contents(contents))
        registry = registry.with_resource(path.as_uri(), Resource.from_contents(contents))
    return registry


def load(path: Path) -> object:
    return json.loads(path.read_text())


def validate(path: Path, schema_name: str) -> object:
    instance = load(path)
    schema_path = SCHEMAS / schema_name
    schema = load(schema_path)
    errors = sorted(
        Draft202012Validator(
            schema, registry=schema_registry(), format_checker=FormatChecker()
        ).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            print(f"{path.relative_to(ROOT)}:{location}: {error.message}", file=sys.stderr)
        raise SystemExit(1)
    return instance


def product_id(brand: str, model: str, variant: str) -> str:
    raw = "\x1f".join(part.strip().casefold() for part in (brand, model, variant))
    return f"product_{hashlib.sha256(raw.encode()).hexdigest()[:20]}"


def validate_catalog() -> None:
    path = ROOT / "data" / "catalog" / "products.json"
    catalog = validate(path, "product-catalog.schema.json")
    ids: set[str] = set()
    keys: set[tuple[str, str, str]] = set()
    for item in catalog["products"]:
        expected_id = product_id(item["brand"], item["model"], item["variant"])
        if item["id"] != expected_id:
            raise SystemExit(f"{path.relative_to(ROOT)}: 잘못된 상품 ID: {item['id']}")
        key = (item["brand"], item["model"], item["variant"])
        if item["id"] in ids or key in keys:
            raise SystemExit(f"{path.relative_to(ROOT)}: 중복 상품: {key}")
        ids.add(item["id"])
        keys.add(key)


def main() -> None:
    validate(ROOT / "config" / "pricing-rules.json", "pricing-rules.schema.json")
    validate_catalog()
    for path in sorted((ROOT / "data" / "raw").glob("*.json")):
        validate(path, "mcp-refresh-raw.schema.json")
    for path in sorted((ROOT / "data" / "imports").glob("*.json")):
        schema = (
            "legacy-price-guide.schema.json"
            if path.name.startswith("legacy-")
            else "listing-import.schema.json"
        )
        validate(path, schema)
    dist = ROOT / "dist" / "data.json"
    payload = load(dist)
    schema = (
        "price-guide-export.schema.json"
        if payload.get("status") == "normalized"
        else "legacy-price-guide.schema.json"
    )
    validate(dist, schema)
    print("JSON Schema validation passed")


if __name__ == "__main__":
    main()
