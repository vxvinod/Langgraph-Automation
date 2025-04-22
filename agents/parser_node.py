import json
import yaml

def extract_properties(schema):
    """Recursively extract schema properties, including constraints."""
    if not schema or not isinstance(schema, dict):
        return {}

    props = schema.get("properties", {})
    extracted = {}

    for name, details in props.items():
        if details.get("type") == "object":
            extracted[name] = {
                "type": "object",
                "properties": extract_properties(details)
            }
        else:
            extracted[name] = {
                "type": details.get("type", "string"),
                "format": details.get("format"),
                "enum": details.get("enum"),
                "minLength": details.get("minLength"),
                "maxLength": details.get("maxLength"),
                "pattern": details.get("pattern"),
                "description": details.get("description")
            }

    return extracted


def parse_api(state: dict) -> dict:
    filepath = state.get("filepath")
    spec = state.get("spec")

    if not spec:
        with open(filepath, 'r') as f:
            spec = json.load(f) if filepath.endswith('.json') else yaml.safe_load(f)

    endpoints = []

    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            parameters = details.get("parameters", [])
            responses = details.get("responses", {})

            request_body = details.get("requestBody", {})
            body_schema = {}
            if request_body:
                content = request_body.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})
                body_schema = extract_properties(schema)

            endpoints.append({
                "method": method.upper(),
                "path": path,
                "summary": details.get("summary", ""),
                "parameters": parameters,
                "request_body_properties": body_schema,
                "responses": responses
            })

    return {"endpoints": endpoints}
