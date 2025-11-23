import requests
import json
import streamlit as st

# The core API execution function (already updated for JWT token)
def call_expense_categorizer_api(transaction_description: str) -> str:
    """Calls the external expense categorizer API with a JWT token."""
   
    api_url = "http://localhost:8000/predict"
    payload = {"transaction": transaction_description}
   
    # Safely retrieve token from session state
    jwt_token = st.session_state.get("id_token")
    if not jwt_token:
        return json.dumps({
            "error": "JWT token is missing from session state.", 
            "type": "Error",
            "category": "Error"
        })
       
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": f"API call failed: {e}", 
            "type": "Error",
            "category": "Error"
        })
    except json.JSONDecodeError:
        return json.dumps({
            "error": "API returned invalid JSON", 
            "type": "Error",
            "category": "Error"
        })

# Mapping is simple, as we'll call this based on the parsed name
AVAILABLE_FUNCTIONS = {
    "categorize_transaction": call_expense_categorizer_api,
}
