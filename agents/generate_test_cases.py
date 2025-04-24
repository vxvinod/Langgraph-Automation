from typing import Dict, List, Any
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI()  # assumes API key is configured in env

def extract_essential_schema(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts only essential field validation info (name, type, enum, min/max, pattern).
    """
    summary = {}
    for field, info in properties.items():
        if info.get("type") == "object" and "properties" in info:
            summary[field] = extract_essential_schema(info["properties"])
        else:
            summary[field] = {
                key: info[key] for key in ["type", "enum", "minLength", "maxLength", "pattern", "default", "minimum", "maximum"] if key in info
            }
    return summary

def format_prompt(api_schema: Dict[str, Any], chunked_schema: Dict[str, Any]) -> str:
    """
    Converts summarized parser_node output into a prompt for the LLM.
    """
    return f"""
You are a testing AI assistant. Generate test cases for the following API endpoint.

API:
- Method: {api_schema['method']}
- Path: {api_schema['path']}
- Request Body (Schema Summary):
{json.dumps(chunked_schema, indent=2)}

Instructions:
- Create both positive, negative test cases and edgecases.
- For each enum field, generate a separate test case for each possible value.
- Include validation edge cases like minLength, maxLength, and pattern violations.
- Each test case must include: description, method, path, payload, expected_status

Output as JSON list of test cases.
"""

def call_llm(prompt: str) -> List[Dict[str, Any]]:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content.strip())

def chunk_properties(properties: Dict[str, Any], chunk_size: int = 5) -> List[Dict[str, Any]]:
    keys = list(properties.keys())
    return [
        {key: properties[key] for key in keys[i:i + chunk_size]}
        for i in range(0, len(keys), chunk_size)
    ]

def generate_test_cases(state: Dict[str, Any]) -> Dict[str, Any]:
    api_endpoints = state.get("endpoints", [])
    all_cases = []

    for endpoint in api_endpoints:
        properties = endpoint.get("request_body_properties", {})
        summarized = extract_essential_schema(properties)
        chunks = chunk_properties(summarized, chunk_size=5)
        for chunk in chunks:
            prompt = format_prompt(endpoint, chunk)
            try:
                test_cases = call_llm(prompt)
                all_cases.extend(test_cases)
            except Exception as e:
                print(f"Error generating test cases for {endpoint['path']}: {e}")

    return {"test_cases": all_cases}
