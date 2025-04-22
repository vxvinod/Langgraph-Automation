from typing import Dict, List, Any
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI()  # assumes API key is configured in env

def format_prompt(api_schema: Dict[str, Any]) -> str:
    """
    Converts parser_node output into a prompt for the LLM.
    """
    return f"""
You are a testing AI assistant. Generate test cases for the following API endpoint.

API:
- Method: {api_schema['method']}
- Path: {api_schema['path']}
- Request Body Properties:
{json.dumps(api_schema.get('request_body_properties', {}), indent=2)}

Instructions:
- Create both positive and negative test cases 
- All postive testcase should have payload with name, basic with all properties like band, passphrase, security, ssid, vlan and advanced with all properties like band_steer and pmf_state.
- For postive testcase payload format should be contain basic with full properties, advanced with full properties and name.
- For postive testcase property should contain only enum values.
- For Post method Include positive case to cover all enums band_steer and include all payloads in all cases. for example band_steer has 3 enums ['low', 'high', 'medium'] generate 3 different postive testcse, first testcase covers 'low' with full payload, second testcase covers 'high' with full payload and third testcase covers 'medium' with full payload.
- For Post method Include positive case to cover all enums in band and include all payloads in all cases. for example band has 6 enums ["2ghz","5ghz","6ghz","5ghz-6ghz", "2ghz-5ghz","2ghz-5ghz-6ghz"] generate 6 different postive testcse.
- For Post method Include positive case to cover all enumns in pmf_state and include all payloads in all cases. for example pmf _statehas 2 enums ["mandatory", "optional"] generate 2 different postive testcse.
- Include edge cases like maxLength, minLength, invalid patterns
- Each test case should include: description, method, path, payload, expected_status

Output as JSON list of test cases.
"""

def call_llm(prompt: str) -> List[Dict[str, Any]]:
    """
    Calls OpenAI to generate test cases from a prompt.
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    # Assume output is a JSON list
    return json.loads(response.choices[0].message.content.strip())

def generate_test_case_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: Takes parser_node output and returns generated test cases.
    """
    api_endpoints = state.get("endpoints", [])
    all_cases = []

    for endpoint in api_endpoints:
        prompt = format_prompt(endpoint)
        try:
            test_cases = call_llm(prompt)
            all_cases.extend(test_cases)
        except Exception as e:
            print(f"Error generating test cases for {endpoint['path']}: {e}")

    return {"test_cases": all_cases}
