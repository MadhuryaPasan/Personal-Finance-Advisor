import streamlit as st
from controller.helpers.auth import *

# streamlit app page configs for set the page title
st.set_page_config(
    page_title="Personal Finance Advisor", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling that works with both light and dark themes
st.markdown("""
    <style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Center the main content */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    
    /* Style for the welcome container */
    .welcome-container {
        text-align: center;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem auto;
        max-width: 600px;
    }
    
    /* Responsive button styling */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    
    /* Feature cards */
    .feature-card {
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

def login():
    # Create columns for centering
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Hero section
        st.markdown("<div class='welcome-container'>", unsafe_allow_html=True)
        
        
        # Welcome message
        st.title("Personal Finance Advisor")
        st.markdown("### Take control of your financial future")
        st.markdown("Track expenses, manage budgets, and achieve your financial goals with ease.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Login section
        if not st.user.is_logged_in:
            st.markdown("---")
            st.markdown("### Get Started")
            st.markdown("Sign in with your Google account to begin your financial journey")
            
            # Login button
            if st.button("🔐 Sign in with Google", type="primary", use_container_width=True):
                st.login()
        else:
            # User is logged in
            email = st.user.email
            token = generate_email_jwt(email)
            st.session_state["id_token"] = token
            st.success(f"✅ Welcome back, {st.user.name}!")
            
            # Auto-redirect with a small delay for user to see the message
            st.markdown("Redirecting to dashboard...")
            st.switch_page("pages/home.py")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Features section
        st.markdown("---")
        st.markdown("### Why Choose Us?")
        
        # Feature highlights in columns
        feat_col1, feat_col2, feat_col3 = st.columns(3)
        
        with feat_col1:
            st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
            st.markdown("### 📊")
            st.markdown("**Smart Analytics**")
            st.markdown("Visualize your spending patterns")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with feat_col2:
            st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
            st.markdown("### 🎯")
            st.markdown("**Goal Tracking**")
            st.markdown("Set and achieve financial goals")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with feat_col3:
            st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
            st.markdown("### 🔒")
            st.markdown("**Secure & Private**")
            st.markdown("Your data is safe with us")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align: center; opacity: 0.6;'>© 2025 Personal Finance Advisor. All rights reserved.</p>", 
            unsafe_allow_html=True
        )

# Run the main function
if __name__ == "__main__":
    login()





















# import streamlit as st
# from controller.helpers.auth import *

# # streamlit app page configs for set the page title
# st.set_page_config(page_title="Personal Finance Advisor", layout="wide" , initial_sidebar_state="collapsed")

# # login section code
# def login():
#     st.subheader("Login")
#     if not st.user.is_logged_in:
#         if st.button("Login with Google"):
#             st.login()
#         # st.switch_page("app.py")
#     else:
#         email = st.user.email
#         token = generate_email_jwt(email)
#         st.session_state["id_token"] = token
#         st.toast("You are logged in")
#         st.switch_page("pages/home.py")

# # register section code
# def register():
#     st.subheader("Register Page")


# # def main():
# #     tab1, tab2 = st.tabs(["Login", "Register"])

# #     with tab1:
# #         login()

# #     with tab2:
# #         register()
    


# # Run the main function
# if __name__ == "__main__":
#     login()



