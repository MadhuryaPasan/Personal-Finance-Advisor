import streamlit as st

st.subheader("Expense Categorization - Test")

import streamlit as st

# ---- Page UI (header / helper text) ----
st.subheader(ese Categorization  - Test")
st.caption("Type an expense in plain text and submit. We’ll handle categorization next.")

st.markdown(
    """
    <div style="
        padding: 14px 16px;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
        ">
        <b>Examples you can type now</b>
        <ul style="margin: 6px 0 0 18px;">
            <li>Diesel 20L – LKR 8,000</li>
            <li>Lunch at canteen – 500</li>
            <li>Dialog bill – 1,950</li>
        </ul>
        <div style="font-size: 12px; color: #6c757d; margin-top: 6px;">
            (Only a single text box and a submit button for now.)
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ---- Simple Form ----
with st.form("expense_text_form", clear_on_submit=True):
    expense_text = st.text_input(
        "Expense description",
        placeholder="e.g., “Groceries at Keells – 2,450”"
    )
    submitted = st.form_submit_button("Submit")

if submitted:
    if expense_text.strip():
        st.success("✅ Received your expense text.")
        st.code(expense_text)
        # Store last submitted (optional small convenience)
        st.session_state["last_expense_text"] = expense_text
    else:
        st.warning("Please enter an expense description before submitting.")

# (Optional) Show last submitted for quick reference
if "last_expense_text" in st.session_state:
    with st.expander("Last submitted"):
        st.write(st.session_state["last_expense_text"])
