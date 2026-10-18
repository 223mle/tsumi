#!/usr/bin/env python3
"""Validate a session-insights result: the JSON schema, the rules a schema cannot say,
and (with --conversation) that every quote really appears in the session.

Usage: check_insights.py [reply_file] [--conversation session_file]
The reply may be raw JSON or text containing a ```json block; the last block wins.
Prints one error per line and exits 1 on any error. Stdlib only.
"""
import json
import pathlib
import re
import sys

SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "references" / "insights.schema.json"
NEEDS_CHECK = {"repeated-correction", "hidden-mistake"}


def extract(text):
    blocks = re.findall(r"```json\s*\n(.*?)\n```", text, re.S)
    raw = blocks[-1] if blocks else text.strip()
    return json.loads(raw)


def validate(value, schema, path, errors):
    """Subset of JSON Schema used by insights.schema.json."""
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


def norm(s):
    return re.sub(r"[\s「」『』\"'“”]+", "", s)


def rules(result, errors, conversation=None):
    """Rules a schema cannot express."""
    ids = [i.get("id") for i in result.get("insights", [])]
    if len(ids) != len(set(ids)):
        errors.append("insights: ids must be unique")
    conv = norm(conversation) if conversation else None
    for ins in result.get("insights", []):
        p = f"insights[{ins.get('id', '?')}]"
        if ins.get("kind") in NEEDS_CHECK and "check" not in ins and "no_check_reason" not in ins:
            errors.append(f"{p}: a {ins['kind']} needs a check proposal or no_check_reason")
        if conv is None:
            continue
        for e in ins.get("evidence", []):
            # A quote may join several turns with " / " or skip text with "…"/"...".
            parts = [x for x in re.split(r"\s/\s|…|\.\.\.", e.get("quote", "")) if norm(x)]
            missing = [x.strip() for x in parts if norm(x) not in conv]
            if missing:
                errors.append(f"{p}: quote not found in the session: {missing[0][:60]!r}")


def check(text, conversation=None):
    errors = []
    try:
        result = extract(text)
    except ValueError as e:
        return [f"no parsable JSON: {e}"]
    validate(result, json.loads(SCHEMA.read_text(encoding="utf-8")), "$", errors)
    if not errors:
        rules(result, errors, conversation)
    return errors


if __name__ == "__main__":
    args, conv = sys.argv[1:], None
    if "--conversation" in args:
        i = args.index("--conversation")
        conv = pathlib.Path(args[i + 1]).read_text(encoding="utf-8")
        del args[i:i + 2]
    text = pathlib.Path(args[0]).read_text(encoding="utf-8") if args else sys.stdin.read()
    errs = check(text, conv)
    for e in errs:
        print(e)
    print("ok" if not errs else f"{len(errs)} error(s)")
    sys.exit(1 if errs else 0)
