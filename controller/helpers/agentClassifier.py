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
    - "add_new_goal": Select this if the user wants to set or create a new financial goal.
    - "get_all_goals": Select this if the user wants to retrieve, list, or show all financial goals.
    - "track_goal": Select this if the user is asking to check or update the progress of a specific financial goal (e.g., “vacation goal progress”, “check my emergency fund goal”, or “I added savings towards a goal”).
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

    7.  If "add_new_goal" is selected:
        - "args" must contain the key "return_query".
        - The value must be a CONCISE SUMMARY of the goal extracted from the user input (e.g., remove verbs like "set a goal for").

    8.  If "get_all_goals" is selected:
        - "args" must contain the key "return_query".
        - The value must be "None" if the user is asking for all goals (e.g., "Show my goals", "Get all goals", "List goals").

    9.  If "track_goal" is selected:
        - "args" must contain the key "return_query".
        - The value must be the EXACT ORIGINAL USER INPUT (e.g., "Tell me about my vacation goal progress", "Tell me about my vacation goal progress and also I saved Rs. 1000 additionally").

    10.  If "general" is selected:
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

    User: Set a goal to save 5000 for vacation
    Response:
    {{
        "tool_name": "add_new_goal",
        "args": {{
            "return_query": "save 5000 for vacation"
        }}
    }}
    User: Set Rs. 5000 for my vacation goal with a deadline of 2025-11-12
    Response:
    {{
        "tool_name": "add_new_goal",
        "args": {{
            "return_query": "save 5000 for vacation"
        }}
    }}
    User: Set Rs. 5000 for my vacation goal with a deadline of 2025-11-12
    Response:
    {{
        "tool_name": "add_new_goal",
        "args": {{
            "return_query": "save 5000 for vacation"
        }}
    }}
    User: Set goal to save Rs 150,000 for car service bt 2022-12-15
    Response:
    {{
        "tool_name": "add_new_goal",
        "args": {{
            "return_query": "save 5000 for vacation"
        }}
    }}

    User: Add a new goal: Emergency fund Rs 10000
    Response:
    {{
        "tool_name": "add_new_goal",
        "args": {{
            "return_query": "Emergency fund Rs 10000"
        }}
    }}

    User: Show me all my goals
    Response:
    {{
        "tool_name": "get_all_goals",
        "args": {{
            "return_query": "None"
        }}
    }}

    User: Get all goals
    Response:
    {{
        "tool_name": "get_all_goals",
        "args": {{
            "return_query": "None"
        }}
    }}

    User: Tell me about my vacation goal progress
    Response:
    {{
        "tool_name": "track_goal",
        "args": {{
            "return_query": "Tell me about my vacation goal progress"
        }}
    }}

    User: Tell me about my vacation goal progress and also i saved Rs. 1000 additionally
    Response:
    {{
        "tool_name": "track_goal",
        "args": {{
            "return_query": "Tell me about my vacation goal progress and also i saved Rs. 1000 additionally"
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
    if raw_content.startswith("json"):
        content = raw_content.lstrip("`\n").lstrip("json\n")
    else:
        content = raw_content

    # 2. Remove the closing markdown block marker
    if content.endswith(""):
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
        elif tool_name == "add_new_goal":
            return_query = user_message
        elif tool_name == "get_all_goals":
            return_query = 'None'

        # print(f"raw: {final_json_string}")
        # print(f"Agent to use: {tool_name}")
        # print(f"Original query: {return_query}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

    return tool_name, return_query



def agent_result_formatter(agent_result):
    system_prompt = f"""
    You are a professional and highly knowledgeable Personal Finance Advisor. 
    Your primary role is to process and present structured financial data to users.

    Follow these instructions precisely:
    1. Always present the provided data in a clear, well-formatted *table* with descriptive headers.
    2. After the table, provide a *concise summary* of the data.
    3. Maintain a *professional and informative tone* at all times.
    4. Do *not* include raw data, code, or JSON in your response. All information must be presented as formatted text.
    5. Ensure that *all details* from the provided data are included in the response.
    6. If you receive an error message, *return it exactly as it is* (e.g., “No items found for this user.”).
    7. If no data is provided, *do not generate or assume any fake data*. Simply state that no data was provided.
    """



    result_json_string = json.dumps(agent_result, indent=4)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": result_json_string},
        ],
        temperature=1.0,
        # seed=42,
    )
    return response.choices[0].message.content.strip()




def agent_responce (user_prompt:str) :
    tool_name, return_query = classify_agent(user_prompt)
    print(tool_name)
    result = ""
    tool_name = tool_name.lower()
    if tool_name == "expense_categorizer":
        payload = {"transaction": return_query}
        response = requests.post(predict_api_url, json=payload, headers=headers)
        result = agent_result_formatter(response.json())
        
        
        
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
        budget_response = requests.get(get_budget_api, json=payload, headers=headers)
        
        response_data = budget_response.json()
        for result in response_data:
            if 'user_id' in result:
                del result['user_id']
        result = agent_result_formatter(f"This is the list of budgets previously entered by the user.  : {response_data}")
        # result = response.json()



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
        
        
        response_data = get_transaction_response.json()
        for result in response_data:
            if 'user_id' in result:
                del result['user_id']
        result = agent_result_formatter(f"This is the list of transactions previously entered by the user.  : {response_data}")
        
        
        
        
        
    elif tool_name == "add_new_transaction":
        payload = {
            "user_id": user_id,
            "user_request": return_query
        }
        add_new_transaction_response = requests.post(
            create_transaction_api, json=payload, headers=headers
        )
        
        response_data = add_new_transaction_response.json()
        if 'user_id' in response_data:
            del response_data['user_id']
        result = agent_result_formatter(f"this is the details of new transaction and this data is succesfully saved : {response_data}")
        
        
        
        
    elif tool_name == "add_new_budget":
        payload = {
            "user_id": user_id,
            "user_request": return_query
        }
        new_budget_response = requests.post(
            create_budget_api, json=payload, headers=headers
        )
        response_data = new_budget_response.json()
        if 'user_id' in response_data:
            del response_data['user_id']
        result = agent_result_formatter(f"this is the details of setting up new budget plan and this data is succesfully saved  : {response_data}")
        
    elif tool_name == "add_new_goal":
        payload = {
        "user_id": user_id,
        "user_request": return_query
        }
        new_goal_response = requests.post(
            create_goal_api, json=payload, headers=headers
        )
        response_data = new_goal_response.json()
        if 'user_id' in response_data:
            del response_data['user_id']
        result = agent_result_formatter(f"this is the details of setting up new Goal and this data is succesfully saved  : {response_data}")
        
    elif tool_name == "get_all_goals":
        payload = {
                    "user_id":user_id
                }
        get_get_response = requests.get(
            get_goal_api, json=payload, headers=headers
        )
        response_data = get_get_response.json()
        for result in response_data:
            if 'user_id' in result:
                del result['user_id']
        result = agent_result_formatter(f"This is the list of goals previously entered by the user.  : {response_data}")
        print(result)
        print(response_data)

    

    elif tool_name == "track_budget":
        payload = {"transaction": return_query}
        response = requests.post(predict_api_url, json=payload, headers=headers)
        classify_agent_result = response.json()
        classify_agent_result_category = classify_agent_result["category"]
        payload = {"user_id": user_id, "type": "", "category": classify_agent_result_category}
        get_transaction_response = requests.get(
            get_transaction_api, json=payload, headers=headers
        )
        get_transaction_result = get_transaction_response.json()

        payload = {
            "budget": {
                # "budget_id": 1,
                "user_id": user_id,
                "category": classify_agent_result_category,
                # "monthly_limit": 500.0,
                # "start_date": "2025-09-01",
                # "current_spent": 0.0,
            },
            "recent_transactions": get_transaction_result,
        }
        track_budget_response = requests.post(
            track_budget_api, json=payload, headers=headers
        )
        response_data = track_budget_response.json()
        result = response_data['suggestion']
        
    elif tool_name == "track_goal": 
        payload = {"user_id": user_id, "type": "", "category": ""}
        get_transaction_response = requests.get(
            get_transaction_api, json=payload, headers=headers
        )
        get_transaction_result = get_transaction_response.json()

        payload = {
                "user_id" : user_id,
                "user_request" : return_query,
                "recent_transactions":get_transaction_result
            }
        track_goal_response = requests.post(
            track_goal_api, json=payload, headers=headers
        )
        response_data = track_goal_response.json()
        result = response_data['suggestion']

    elif tool_name == "general":
        SYSTEM_MESSAGE = {
            "role": "system",
            "content": (
                "You are a **Personal Finance Advisor**. Your job is to provide accurate, practical, and clear guidance "
                "strictly on personal finance topics. This includes:\n"
                "- Budgeting and expense tracking\n"
                "- Saving strategies and financial goals\n"
                "- Spending analysis and financial planning\n"
                "- Investing and retirement planning\n"
                "- Taxes, insurance, debt, and credit management\n"
                "- Financial products and responsible money management\n\n"
                
                "If a user request is **outside personal finance**, respond with:\n"
                "'I can only help with personal finance topics. Please ask about budgeting, saving, investing, debt, taxes, insurance, or credit.'\n\n"
                
                "You must follow these **Responsible AI Guidelines**:\n"
                "1. **Accuracy & Honesty** – Only provide information you are confident is correct. If unsure, clearly say so.\n"
                "2. **No Legal or Personalized Tax Advice** – Provide general guidance only; do not give legal or individualized tax instructions.\n"
                "3. **Transparency** – Clearly state any assumptions made when forming a response.\n"
                "4. **Safety & Neutrality** – Avoid discriminatory, biased, or harmful financial advice. Keep recommendations factual and neutral.\n"
                "5. **Clarity & Practicality** – Keep answers concise, structured, and actionable.\n\n"
                
                "### What this model can do:\n"
                "This model can help users **categorize transactions**, **set and track budgets**, **manage and review financial goals**, "
                "and **analyze personal spending patterns**. It can provide practical tips to improve budgeting and saving, offer insights "
                "on financial habits, and summarize financial data clearly. It acts as a personal finance assistant for everyday money management."
            ),
        }
        response = client.chat.completions.create(
            model=model,
            messages=[
                SYSTEM_MESSAGE,
                *[
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.messages
                ],
            ],
            stream=True,
        )
        result = st.write_stream(response)
        # response = client.chat.completions.create(
        #     model=model,
        #     messages=[
        #         {"role": "system", "content": "You are a financial assistant."},
        #         {"role": "user", "content": return_query},
        #     ],
        # )
        # result = response.choices[0].message.content.strip()
    else:
        result = "Something went wrong. Tool selection failed. Please try again later."
    
    return result