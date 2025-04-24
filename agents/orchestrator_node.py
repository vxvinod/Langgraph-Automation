# orchestrator_node.py
import json
from maestroIQ.maestro_test_agent.agents.parser_node import parse_api
from maestroIQ.maestro_test_agent.agents.rag_query_node import retrieve_example_payload
from typing import Dict, Any
import openai
from dotenv import load_dotenv

load_dotenv()

MAX_TOKENS_LIMIT = 7800  # leave buffer for system + formatting
openai = openai.OpenAI()

def truncate_json(json_obj, max_keys=10):
    if isinstance(json_obj, dict):
        return {k: truncate_json(v, max_keys) for i, (k, v) in enumerate(json_obj.items()) if i < max_keys}
    elif isinstance(json_obj, list):
        return json_obj[:max_keys]
    else:
        return json_obj

def count_tokens(text: str) -> int:
    return len(text.split())

def truncate_schema(schema: Dict[str, Any], max_fields: int = 5) -> Dict[str, Any]:
    return {k: schema[k] for i, k in enumerate(schema) if i < max_fields}

def format_prompt(endpoint: Dict[str, Any], example_payload: Dict[str, Any]) -> str:
    schema = endpoint.get("request_body_properties", {}).copy()
    trimmed_payload = example_payload.copy()

    def safe_json(obj):
        try:
            return json.dumps(obj, indent=2)
        except Exception:
            return str(obj)

    while True:
        schema_summary = safe_json(schema)
        payload_summary = safe_json(trimmed_payload)

        prompt = f"""
You are a testing AI assistant. Generate test cases for the following API endpoint:
- Method: {endpoint['method']}
- Path: {endpoint['path']}

Schema:
{schema_summary}

Example Payload:
{payload_summary}

Instructions:
- Generate test cases covering all enum values
- Include positive, negative, edge cases (lengths, pattern)
- Return as JSON list of: description, method, path, payload, expected_status
"""
        tokens = count_tokens(prompt)
        if tokens <= MAX_TOKENS_LIMIT:
            break

        print(f"⚠️ Prompt too long ({tokens} tokens). Trimming...")

        if isinstance(schema, dict) and len(schema) > 1:
            schema = {k: schema[k] for i, k in enumerate(schema) if i < len(schema) - 1}
        elif isinstance(trimmed_payload, dict) and len(trimmed_payload) > 1:
            trimmed_payload = truncate_json(trimmed_payload, max_keys=len(trimmed_payload) - 1)
        else:
            print("⚠️ Trimming reached minimum. Using smallest possible prompt.")
            break

    return prompt

def call_llm(prompt: str):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content.strip())

def generate_test_cases_rag():
    state = parse_api({"filepath": "data/full_wlan.json"})
    all_test_cases = []
    for endpoint in state["endpoints"]:
        for wlan_type in ["wpa2-wpa3-psk"]:
            #example_payload = retrieve_example_payload(endpoint["path"], endpoint["method"], wlan_type)
            example_payload = retrieve_example_payload('/wifi_enterprise/wlans', endpoint["method"], wlan_type)
            prompt = format_prompt(endpoint, example_payload)
            try:
                cases = call_llm(prompt)
                all_test_cases.extend(cases)
            except Exception as e:
                print(f"Failed to generate test cases for {endpoint['path']}: {e}")
    return {"test_cases": all_test_cases}

if __name__ == "__main__":
    result = generate_test_cases_rag()
    with open("new_generated_testcase.txt", 'w') as f:
        f.write(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
