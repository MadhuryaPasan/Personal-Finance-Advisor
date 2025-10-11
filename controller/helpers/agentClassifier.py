import streamlit as st
from openai import OpenAI
import json
import requests


id_token = st.session_state["id_token"]
user_id=st.user.sub
headers = {"Authorization": f"Bearer {id_token}"}


predict_api_url = "http://localhost:8000/predict"
track_budget_api = "http://localhost:8000/track_budget"
get_budget_api = "http://localhost:8000/get_budgets"
create_budget_api = "http://localhost:8000/set_budget"

track_goal_api = "http://localhost:8000/track_goal"
get_goal_api = "http://localhost:8000/get_goals"
create_goal_api = "http://localhost:8000/create_goal"

create_transaction_api = "http://localhost:8000/create_transaction"
get_transaction_api = "http://localhost:8000/get_transactions"

client = OpenAI(
    base_url="http://localhost:11434/v1",  # URL of the Ollama server
    api_key="dummy_key",  # Add a dummy value
)

model = "gemma3:1b"


def classify_agent(user_message: str) -> str:
    """
    Uses Gemma 3 to decide which tool need to use
    """
    system_prompt = f"""
You are an agent selector designed to classify user requests into one of the available agents.
You MUST respond with a single, valid JSON object, with absolutely no markdown, extra text, or conversation outside of the JSON.

Available agents:
- "expense_categorizer": Select this if the user is asking to categorize, classify, or analyze a financial transaction or expense.
- "all_budget_details": Select this if the user is asking to retrieve or show budget details for a specific category or all categories.
- "get_all_transactions": Select this if the user is asking to retrieve or show transactions for a specific category or all categories.
- "add_new_transaction": Select this if the user wants to add a new transaction (expense or income).
- "add_new_budget": Select this if the user wants to create or set a new budget for a category or period.
- "track_budget": Select this if the user wants to check budget progress, remaining balance, or track spending vs. budget.
- "general": Select this for all other requests, including general conversation, questions, or advice.


TOOL OUTPUT FORMAT:
Output ONLY a single, valid JSON object (no markdown, no extra text).

1.  If "expense_categorizer" is selected:
    - "args" must contain the key "return_query".
    - The value must be a CONCISE SUMMARY of the transaction extracted from the user input (remove classifying verbs like "categorize this").

2.  If "all_budget_details" is selected:
    - If the user specifies a category (one of ["Food", "Transport", "Rent", "Entertainment", "Shopping", "Bills", "Salary", "Freelance", "Sale", "Investment", "Refund"]), return the EXACT ORIGINAL USER INPUT for "return_query".
    - If the user requests all budget details without specifying a category (e.g., "Show me all budget details", "Show me my budget details", "Show budget"), you MUST set "return_query" to the string "None".

3.  If "get_all_transactions" is selected:
    - If the user specifies a category (one of ["Food", "Transport", "Rent", "Entertainment", "Shopping", "Bills", "Salary", "Freelance", "Sale", "Investment", "Refund"]), return the EXACT ORIGINAL USER INPUT for "return_query".
    - If the user requests all transactions without a category (e.g., "Show me all transactions", "Show transactions"), you MUST set "return_query" to the string "None".

4.  If "add_new_transaction" is selected:
    - "args" must contain the key "return_query".
    - The value must be a CONCISE SUMMARY of the transaction extracted from the user input (remove classifying verbs like "Add this").

5.  If "add_new_budget" is selected:
    - "args" must contain the key "return_query".
    - The value must be a CONCISE SUMMARY of the transaction extracted from the user input (remove classifying verbs like "Add this").

6.  If "track_budget" is selected:
    - "args" must contain the key "return_query".
    - The value must be the EXACT ORIGINAL USER INPUT.

7.  If "general" is selected:
    - "args" must contain the key "return_query".
    - The value must be the EXACT ORIGINAL USER INPUT.


EXAMPLES:

User: categorize this car service rs 1000
Response:
{{
    "tool_name": "expense_categorizer",
    "args": {{
        "return_query": "car service rs 1000"
    }}
}}

User: please classify this transaction - lunch 500
Response:
{{
    "tool_name": "expense_categorizer",
    "args": {{
        "return_query": "lunch 500"
    }}
}}

User: Show me my Food budget
Response:
{{
    "tool_name": "all_budget_details",
    "args": {{
        "return_query": "Show me my Food budget"
    }}
}}

User: Show me my budget details
Response:
{{
    "tool_name": "all_budget_details",
    "args": {{
        "return_query": "None"
    }}
}}

User: Show all budget details
Response:
{{
    "tool_name": "all_budget_details",
    "args": {{
        "return_query": "None"
    }}
}}

User: Show budget
Response:
{{
    "tool_name": "all_budget_details",
    "args": {{
        "return_query": "None"
    }}
}}

User: Show me my Food transactions
Response:
{{
    "tool_name": "get_all_transactions",
    "args": {{
        "return_query": "Show me my Food transactions"
    }}
}}

User: Show me all transactions
Response:
{{
    "tool_name": "get_all_transactions",
    "args": {{
        "return_query": "None"
    }}
}}

User: Add a new transaction: Salary 5000
Response:
{{
    "tool_name": "add_new_transaction",
    "args": {{
        "return_query": "Salary 5000"
    }}
}}

User: Set a new budget for Food Rs 1000
Response:
{{
    "tool_name": "add_new_budget",
    "args": {{
        "return_query": "Foods for Rs 1000"
    }}
}}

User: Track my Transport budget
Response:
{{
    "tool_name": "track_budget",
    "args": {{
        "return_query": "Track my Transport budget"
    }}
}}

User: How are you?
Response:
{{
    "tool_name": "general",
    "args": {{
        "return_query": "How are you?"
    }}
}}

User: Tell me a joke about money.
Response:
{{
    "tool_name": "general",
    "args": {{
        "return_query": "Tell me a joke about money."
    }}
}}

User: What is the definition of inflation?
Response:
{{
    "tool_name": "general",
    "args": {{
        "return_query": "What is the definition of inflation?"
    }}
}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        # seed=42,
        response_format={"type": "json_object"},
    )
    raw_content = response.choices[0].message.content.strip()

    # 1. Remove the opening markdown block marker
    if raw_content.startswith("```json"):
        content = raw_content.lstrip("`\n").lstrip("json\n")
    else:
        content = raw_content

    # 2. Remove the closing markdown block marker
    if content.endswith("```"):
        final_json_string = content.rstrip("`")
    else:
        final_json_string = content

    json_string = final_json_string

    try:
        result_dict = json.loads(json_string)

        # Extract the required information
        tool_name = result_dict.get("tool_name")
        return_query = result_dict.get("args", {}).get("return_query")
        if tool_name == "general":
            return_query = user_message
        elif tool_name == "all_budget_details":
            if (
                return_query == "None"
                or return_query == "none"
                or return_query == None
                or return_query == ""
            ):
                return_query = "None"
            else:
                return_query = user_message
        elif tool_name == "get_all_transactions":
            if (
                return_query == "None"
                or return_query == "none"
                or return_query == None
                or return_query == ""
            ):
                return_query = "None"
            else:
                return_query = user_message
        elif tool_name == "track_budget":
            return_query = user_message

        # print(f"raw: {final_json_string}")
        # print(f"Agent to use: {tool_name}")
        # print(f"Original query: {return_query}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

    return tool_name, return_query







def agent_responce (user_prompt:str) :
    tool_name, return_query = classify_agent(user_prompt)
    result = ""
    tool_name = tool_name.lower()
    if tool_name == "expense_categorizer":
        payload = {"transaction": return_query}
        response = requests.post(predict_api_url, json=payload, headers=headers)
        result = response.json()
    elif tool_name == "all_budget_details":
        category = ""
        if return_query == "None" or return_query == "none":
            category = ""
        else:
            payload = {"transaction": return_query}
            response = requests.post(predict_api_url, json=payload, headers=headers)
            classify_agent_result = response.json()
            category = classify_agent_result["category"]
        payload = {"user_id": user_id, "category": category}
        response = requests.get(get_budget_api, json=payload, headers=headers)
        result = response.json()

    elif tool_name == "get_all_transactions":
        category = ""
        type = ""
        if return_query == "None" or return_query == "none":
            category = ""
            type = ""
        else:
            payload = {"transaction": return_query}
            response = requests.post(predict_api_url, json=payload, headers=headers)
            classify_agent_result = response.json()
            category = classify_agent_result["category"]
            type = classify_agent_result["type"]
        payload = {"user_id": user_id, "type": type, "category": category}
        get_transaction_response = requests.get(
            get_transaction_api, json=payload, headers=headers
        )
        result = get_transaction_response.json()
    elif tool_name == "add_new_transaction":
        payload = {
            "user_id": user_id,
            "user_request": return_query
        }
        add_new_transaction_response = requests.post(
            create_transaction_api, json=payload, headers=headers
        )
        result = add_new_transaction_response.json()
    elif tool_name == "add_new_budget":
        payload = {
            "user_id": user_id,
            "user_request": return_query
        }
        track_budget_response = requests.post(
            create_transaction_api, json=payload, headers=headers
        )
        result = track_budget_response.json()

    elif tool_name == "track_budget":
        payload = {"transaction": return_query}
        response = requests.post(predict_api_url, json=payload, headers=headers)
        classify_agent_result = response.json()
        classify_agent_result_category = classify_agent_result["category"]
        payload = {"user_id": user_id, "type": "", "category": "Transport"}
        get_transaction_response = requests.get(
            get_transaction_api, json=payload, headers=headers
        )
        get_transaction_result = get_transaction_response.json()

        payload = {
            "budget": {
                "budget_id": 1,
                "category": "Transport",
                "monthly_limit": 500.0,
                "start_date": "2025-09-01",
                "current_spent": 0.0,
            },
            "recent_transactions": get_transaction_result,
        }
        track_budget_response = requests.post(
            track_budget_api, json=payload, headers=headers
        )
        result = track_budget_response.json()

    elif tool_name == "general":
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a financial assistant."},
                {"role": "user", "content": return_query},
            ],
        )
        result = response.choices[0].message.content.strip()
    print(result)
    print()
    print(tool_name, return_query)