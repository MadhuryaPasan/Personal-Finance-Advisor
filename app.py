import streamlit as st
from controller.helpers.auth import *

# streamlit app page configs for set the page title
st.set_page_config(page_title="Personal Finance Advisor", layout="wide" , initial_sidebar_state="collapsed")

# login section code
def login():
    st.subheader("Login")
    if not st.user.is_logged_in:
        if st.button("Login with Google"):
            st.login()
        # st.switch_page("app.py")
    else:
        email = st.user.email
        token = generate_email_jwt(email)
        st.session_state["id_token"] = token
        st.toast("You are logged in")
        st.switch_page("pages/home.py")

# register section code
def register():
    st.subheader("Register Page")


def main():
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        login()

    with tab2:
        register()
    


# Run the main function
if __name__ == "__main__":
    main()



