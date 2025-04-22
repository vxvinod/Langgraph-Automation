from openai import OpenAI
import json
import os
import time
from dotenv import load_dotenv
import logging
load_dotenv()
# Setup basic logging
logging.basicConfig(level=logging.INFO)

client = OpenAI()
def call_gpt_with_retry(prompt, max_retries=3, delay=3):
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"[GPT] Attempt {attempt}: Sending prompt...")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            logging.info("[GPT] Response received.")
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"[GPT] Error on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise
            time.sleep(delay)

def generate_pytest_code(state: dict) -> dict:
    test_cases = state.get("test_cases", [])
    generated_code = ""

    for test in test_cases:
        description = test["description"]
        method = test["method"].lower()
        path = test["path"]
        payload = test.get("payload", {})
        expected_status = test.get("expected_status", 200)

        prompt = f"""
You are an expert Python test automation engineer.
Generate a Pytest test function using the 'requests' library for the following test case:

Description: {description}
Method: {method.upper()}
Endpoint: {path}
Payload: {json.dumps(payload, indent=2)}
Expected Status: {expected_status}

Follow these rules:
- Use BASE_URL as the base (do not hardcode the full URL)
- The test function name should be auto-generated from the description
- Use json=payload in requests.post()
- Assert status code
- Add comments for clarity

Return only the Python function definition.
"""

        function_code = call_gpt_with_retry(prompt)
        generated_code += f"\n{function_code}\n"

    # Add import/header
    full_code = f"""import pytest
import requests

BASE_URL = \"https://qa-us-east-1-srv-4.cloud.cambiumnetworks.com/api/v2\"  # Update as needed
{generated_code}
"""

    return {"pytest_code": full_code}
