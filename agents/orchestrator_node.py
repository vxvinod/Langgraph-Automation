# orchestrator_node.py
import json
from maestroIQ.maestro_test_agent.agents.parser_node import parse_api
from maestroIQ.maestro_test_agent.agents.rag_query_node import retrieve_example_payload
from typing import Dict, Any
import openai
from dotenv import load_dotenv
import tiktoken
from tqdm import tqdm

load_dotenv()
openai = openai.OpenAI()

encoding = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

def chunk_schema(schema: dict, max_fields=5):
    keys = list(schema.keys())
    return [dict((k, schema[k]) for k in keys[i:i+max_fields]) for i in range(0, len(keys), max_fields)]

def trim_prompt_content(prompt: str) -> str:
    if "Schema (partial):" in prompt and "Instructions:" in prompt:
        schema_start = prompt.index("Schema (partial):")
        instructions_start = prompt.index("Instructions:")
        return prompt[:schema_start] + prompt[instructions_start:]
    elif "Example payload:" in prompt and "Instructions:" in prompt:
        payload_start = prompt.index("Example payload:")
        instructions_start = prompt.index("Instructions:")
        return prompt[:payload_start] + prompt[instructions_start:]
    lines = prompt.strip().split("\n")
    if len(lines) > 15:
        return "\n".join(lines[:-10])
    else:
        return "\n".join(lines[:5])

def safe_llm_call(prompt: str) -> str:
    max_attempts = 5
    for attempt in range(max_attempts):
        tokens = count_tokens(prompt)
        if tokens <= 7800:
            break
        print(f"⚠️ Attempt {attempt+1}: prompt too long ({tokens} tokens), trimming...")
        prompt = trim_prompt_content(prompt)
    else:
        raise ValueError("❌ Could not reduce prompt size enough after multiple attempts")

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content

def safe_json_parse(text):
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        print("⚠️ JSON Decode Error:", e)
        print("🧪 Trying to recover partial JSON...")
        fixed = text.strip()
        if fixed.endswith(","):
            fixed = fixed[:-1]
        if not fixed.endswith("]"):
            fixed += "]"
        try:
            return json.loads(fixed)
        except Exception as err:
            print("❌ Failed to recover JSON:", err)
            return []

def generate_abstract_tests(endpoint, schema_chunk):
    example_payload = retrieve_example_payload(endpoint["path"], endpoint["method"], "wpa2-wpa3-psk")
    prompt = f"""
You are a test case generator.

API Endpoint:
- Method: {endpoint['method']}
- Path: {endpoint['path']}

Refer to the schema below for rules:
{schema_chunk}

Only use fields that exist in this example payload:
{example_payload}

Instructions:
- For each **enum field**, generate a separate test case for **each value**
- For each **integer or string field** with min/max or minLength/maxLength, generate:
  - One test for the **minimum valid value**
  - One for the **maximum valid value**
  - One for a **value just outside the valid range** (invalid boundary)
- For each field with a **pattern**, generate:
  - One test with a **valid pattern match**
  - One test with an **invalid pattern** that should fail
- Include positive and negative test cases clearly.
- Generate positive, negative, and edge test cases.
- Only include combinations using fields in the example payload.
- Refer to schema for enums, min/max values, and patterns.
- For each enum, generate one case per value.
- For edge cases, create cases with boundary values or invalid patterns.
- Output: JSON list with description, field, enum value (if applicable), rule used, and test type.

Only return raw JSON without any explanation or code block formatting.
"""
    content = safe_llm_call(prompt)
    return safe_json_parse(content)

def generate_concrete_payload(abstract_test, example_payload):
    prompt = f"""
Generate a concrete payload for the following test scenario:

Test scenario:
{json.dumps(abstract_test, indent=2)}

Example payload:
{json.dumps(example_payload, indent=2)}

Instructions:
- Modify only fields relevant to the test scenario.
- Maintain payload structure from example.
- Only return raw JSON. No markdown/code blocks or explanations.

Output: concrete JSON payload.
"""
    content = safe_llm_call(prompt)
    return safe_json_parse(content)

def generate_full_test_cases(endpoint, wlan_type):
    example_payload = retrieve_example_payload(endpoint["path"], endpoint["method"], wlan_type)
    schema_chunks = chunk_schema(endpoint["request_body_properties"], max_fields=5)

    all_concrete_tests = []

    for chunk in tqdm(schema_chunks, desc=f"Processing {endpoint['path']}"):
        try:
            abstract_tests = generate_abstract_tests(endpoint, chunk)
        except ValueError:
            print("⚠️ Chunk too big, splitting further...")
            abstract_tests = []
            sub_chunks = chunk_schema(chunk, max_fields=2)
            for sub_chunk in sub_chunks:
                try:
                    abstract_tests += generate_abstract_tests(endpoint, sub_chunk)
                except ValueError:
                    print("❌ Skipped sub-chunk: still too large.")
                    continue
        for abstract_test in abstract_tests:
            concrete_payload = generate_concrete_payload(abstract_test, example_payload)
            all_concrete_tests.append({
                "description": abstract_test["description"],
                "method": endpoint["method"],
                "path": endpoint["path"],
                "payload": concrete_payload,
                "expected_status": 200 if abstract_test["test_type"] == "positive" else 400
            })

    return all_concrete_tests

if __name__ == "__main__":
    state = parse_api({"filepath": "data/full_wlan.json"})
    results = []
    for endpoint in tqdm(state["endpoints"], desc="Generating test cases"):
        tests = generate_full_test_cases(endpoint, "wpa2-wpa3-psk")
        results.extend(tests)

    with open("generated_test_cases.json", 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Generated {len(results)} test cases.")
