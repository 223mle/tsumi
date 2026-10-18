#!/usr/bin/env python3
"""Validate a mistake-triage result: the JSON schema plus the routing rules.

Usage: check_triage.py [file]   (reads stdin when no file is given)
The input may be raw JSON or text containing a ```json fenced block; the last
block wins. Prints one error per line and exits 1 on any error. Stdlib only.
"""
import json
import pathlib
import re
import sys

SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "references" / "triage.schema.json"


def extract(text):
    blocks = re.findall(r"```json\s*\n(.*?)\n```", text, re.S)
    raw = blocks[-1] if blocks else text.strip()
    return json.loads(raw)


def validate(value, schema, path, errors):
    """Subset of JSON Schema used by triage.schema.json."""
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
        return
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int}
    if t and not (isinstance(value, types[t]) and not (t == "integer" and isinstance(value, bool))):
        errors.append(f"{path}: expected {t}")
        return
    if t == "object":
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing {key}")
        for key, v in value.items():
            if key in props:
                validate(v, props[key], f"{path}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected key {key}")
    elif t == "array":
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems") and len(value) != len({json.dumps(v, sort_keys=True) for v in value}):
            errors.append(f"{path}: items must be unique")
        for i, v in enumerate(value):
            validate(v, schema.get("items", {}), f"{path}[{i}]", errors)
    elif t == "string":
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: empty string")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    elif t == "integer" and value < schema.get("minimum", value):
        errors.append(f"{path}: below minimum {schema['minimum']}")


def rules(result, errors):
    """Routing rules that a schema cannot express."""
    for m in result.get("mistakes", []):
        p = f"mistakes[{m.get('id', '?')}]"
        routes = set(m.get("routes", []))
        for route in routes:
            if route not in m:
                errors.append(f"{p}: route '{route}' needs a '{route}' object")
        for key in ("mechanism", "prose", "eval", "ask"):
            if key in m and key not in routes:
                errors.append(f"{p}: has a '{key}' object but '{key}' is not in routes")
        total = m.get("count_in_conversation", 0) + m.get("count_in_log", 0)
        if total >= 2 and "mechanism" not in routes and "no_mechanism_reason" not in m:
            errors.append(f"{p}: seen {total} times; route to mechanism or give no_mechanism_reason")
        if "prose" in routes and "eval" not in routes and "no_eval_reason" not in m:
            errors.append(f"{p}: a prose fix needs an eval route or no_eval_reason, since nothing fails when prose is skipped")


def check(text):
    errors = []
    try:
        result = extract(text)
    except ValueError as e:
        return [f"no parsable JSON: {e}"]
    validate(result, json.loads(SCHEMA.read_text(encoding="utf-8")), "$", errors)
    if not errors:
        rules(result, errors)
    return errors


if __name__ == "__main__":
    text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else sys.stdin.read()
    errs = check(text)
    for e in errs:
        print(e)
    print("ok" if not errs else f"{len(errs)} error(s)")
    sys.exit(1 if errs else 0)
