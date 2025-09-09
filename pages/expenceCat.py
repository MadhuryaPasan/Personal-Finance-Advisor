import streamlit as st
import requests
import json

# Streamlit app title
st.subheader("Expense Categorization - Test")

# ! delete this for final production
st.markdown(f"for testing (JWT token) : {st.session_state["id_token"]}")


# Input field for transaction text
transaction_input = st.text_input("Enter transaction description:", placeholder="e.g., Coffee at Starbucks")

# Button to trigger prediction
if st.button("Predict"):
    # Check if transaction input is provided
    if not transaction_input:
        st.error("Please enter a transaction description.")
    else:
        # Get JWT token from session state
        id_token = st.session_state.get("id_token", None)
        if not id_token:
            st.error("No JWT token found. Please authenticate.")
        else:
            # API endpoint URL (replace with your FastAPI server URL)
            api_url = "http://localhost:8000/predict"  # Update with your API URL

            # Prepare the request payload
            payload = {"transaction": transaction_input}

            # Set headers with JWT token
            headers = {"Authorization": f"Bearer {id_token}"}

            try:
                # Make POST request to FastAPI endpoint
                response = requests.post(api_url, json=payload, headers=headers)

                # Check if request was successful
                if response.status_code == 200:
                    result = response.json()
                    st.success("Prediction successful!")
                    st.write("*Type:* " + result.get("type", "N/A"))
                    st.write("*Category:* " + result.get("category", "N/A"))
                    st.write("*Amount:* " + str(result.get("amount", "N/A")))
                else:
                    st.error(f"API request failed: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Error calling API: {str(e)}")