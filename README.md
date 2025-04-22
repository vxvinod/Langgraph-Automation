🔍 JSON Block:
json
Copy
Edit
{
  "name": "id",
  "in": "path",
  "required": true,
  "schema": {
    "type": "integer"
  }
}
🧠 Field-by-Field Breakdown:

Field	Meaning
"name": "id"	The name of the parameter. This will be used in the URL, query, etc.
"in": "path"	Where this parameter appears in the HTTP request. In this case: part of the URL path (like /users/{id})
"required": true	Whether the parameter is mandatory for the API call to succeed. If true, the API will fail if this is missing.
"schema"	Defines the expected data type, format, constraints, etc. Here it says it's an integer.
🔁 Common "in" Values:

Value	Meaning
"path"	Appears inside the URL (e.g. /users/{id})
"query"	Appears in the query string (e.g. /users?sort=name)
"header"	Sent in request headers
"cookie"	Sent as a cookie
✅ Real URL Example:
Given this OpenAPI spec:

json
Copy
Edit
{
  "name": "id",
  "in": "path",
  "required": true,
  "schema": { "type": "integer" }
}
This means the endpoint is something like:

bash
Copy
Edit
GET /users/{id}
And calling it would look like:

bash
Copy
Edit
GET /users/123
Where 123 is the id provided in the path.

1. Input Parser Node
Parses OpenAPI schema or server logs

Extracts endpoints, methods, params, responses

2. Test Case Generator Node
Uses GPT + few-shot prompting to generate test cases

Can be RAG-based using previous test templates

3. Code Generator Node
Generates Pytest functions using OpenAI or Code LLMs

Validates schema using Pydantic models

4. Test Executor Node
Runs the generated Pytest scripts

Captures output and generates logs/reports

5. Analyzer Node
Reads log files using Pandas

Uses GPT to summarize failures, flaky tests, coverage gaps