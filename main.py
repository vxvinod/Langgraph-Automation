import json

from langgraph.graph import StateGraph, END
from agents.parser_node import parse_api
from agents.generate_test_cases import generate_test_case_node
from agents.code_generator import generate_pytest_code
from dotenv import load_dotenv

load_dotenv()
builder = StateGraph(dict)
builder.add_node("parser", parse_api)
builder.add_node("generator", generate_test_case_node)
builder.add_node("codegen", generate_pytest_code)
builder.add_edge("parser", "generator")
builder.add_edge("generator", "codegen")
builder.set_entry_point("parser")
builder.set_finish_point("codegen")






graph = builder.compile()

result = graph.invoke({"filepath": "data/wlan.json"})
with open("generated_tests.py", "w") as f:
    f.write(result["pytest_code"])
#print(json.dumps(result, indent=4))