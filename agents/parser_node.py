import json
import yaml

def extract_properties(schema):
    """Recursively extract schema properties, including constraints."""
    if not schema or not isinstance(schema, dict):
        return {}

    props = schema.get("properties", {})
    extracted = {}

    for name, details in props.items():
        # Handle nested objects (recursive extraction)
        if details.get("type") == "object":
            extracted[name] = {
                "type": "object",
                "properties": extract_properties(details)
            }
        else:
            # Extract relevant fields for each property
            extracted[name] = {
                "type": details.get("type", "string"),  # Default type to string if not provided
                "enum": details.get("enum"),  # Enum values if any
                "minLength": details.get("minLength"),  # Minimum length for strings
                "maxLength": details.get("maxLength"),  # Maximum length for strings
                "pattern": details.get("pattern"),  # Regex pattern for validation
                "default": details.get("default"),  # Default value for the property
                "minimum": details.get("minimum"),  # Minimum value for numbers
                "maximum": details.get("maximum"),  # Maximum value for numbers
                "description": details.get("description")  # Field description (optional)
            }

    return extracted


def parse_api(state: dict) -> dict:
    """Parse OpenAPI spec and extract relevant information for endpoints."""
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

            # Adding parsed information to the endpoints list
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "summary": details.get("summary", ""),
                "parameters": parameters,
                "request_body_properties": body_schema,
                "responses": responses
            })

    return {"endpoints": endpoints}

