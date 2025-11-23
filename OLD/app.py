import streamlit as st
from controller.helpers.auth import *
import base64

# Path to your local image
image_path = "images/background.jpg"

# Encode image to base64
with open(image_path, "rb") as f:
    data = f.read()
encoded_image = base64.b64encode(data).decode()

# Streamlit app page configs
st.set_page_config(
    page_title="Personal Finance Advisor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS for better UX
st.markdown(f"""
    <style>
    /* Hide default streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Page background with improved overlay */
    .stApp {{
        background-image: 
            linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)),
            url("data:image/jpeg;base64,{encoded_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Main container with better spacing */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        
    }}

    /* Welcome container with glass effect */
    .welcome-container {{
        text-align: center;
        padding: 3rem 2rem;
        border-radius: 15px;
        margin: 1rem auto 2rem;
        max-width: 700px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }}

    /* Title styling */
    .main-title {{

        background: rgba(255, 255, 255, 1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
    }}

    /* Subtitle styling */
    .subtitle {{
        font-size: 1.3rem;
        color: #e0e0e0;
        margin-bottom: 0.5rem;
        font-weight: 500;
        text-align: center;
    }}

    .description {{
        font-size: 1rem;
        color: #b0b0b0;
        line-height: 1.6;
        text-align: center;
    }}

    /* Enhanced button styling */
    .stButton > button {{
        width: 100%;
        padding: 1rem 2rem;
        font-size: 1.15rem;
        font-weight: 600;
        border-radius: 12px;
        margin-top: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }}

    /* Feature cards with improved design */
    .feature-card {{
        padding: 0.5rem 0.5rem;
        border-radius: 12px;
        margin: 0.5rem 0.5rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        height: 200%;
    }}

    .feature-card:hover {{
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }}

    .feature-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
    }}

    .feature-title {{
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }}

    .feature-text {{
        font-size: 0.95rem;
        color: #c0c0c0;
        line-height: 1.5;
    }}

    /* Login section styling */
    .login-section {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
    }}

    .section-title {{
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
        text-align: center;
    }}

    .section-subtitle {{
        font-size: 1rem;
        color: #b0b0b0;
        text-align: center;
        margin-bottom: 1rem;
    }}

    /* Success message styling */
    .stSuccess {{
        background: rgba(76, 175, 80, 0.2);
        border: 1px solid rgba(76, 175, 80, 0.5);
        border-radius: 8px;
    }}

    /* Divider styling */
    hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        margin: 2rem 0;
    }}

    /* Footer styling */
    .footer {{
        text-align: center;
        color: #808080;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }}

    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .main-title {{
            font-size: 2rem;
        }}
        .subtitle {{
            font-size: 1.1rem;
        }}
        .welcome-container {{
            padding: 2rem 1.5rem;
        }}
        .feature-card {{
            margin: 1rem 0;
        }}
    }}
    </style>
""", unsafe_allow_html=True)


def login():
    # Create columns for centering
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Hero section with enhanced styling
        # st.markdown("<div class='welcome-container'>", unsafe_allow_html=True)

        st.markdown("<h1 class='main-title'>Personal Finance Advisor</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Take Control of Your Financial Future</p>", unsafe_allow_html=True)
        st.markdown(
            "<p class='description'>Track expenses, manage budgets, and achieve your financial goals with powerful insights and easy-to-use tools.</p>",
            unsafe_allow_html=True)

        # st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        # Login section
        if not st.user.is_logged_in:
            # st.markdown("<div class='login-section'>", unsafe_allow_html=True)
            st.markdown("<h2 class='section-title'>Get Started</h2>", unsafe_allow_html=True)
            st.markdown(
                "<p class='section-subtitle'>Sign in with your Google account to begin your financial journey</p>",
                unsafe_allow_html=True)

            # Login button with icon
            if st.button("🔐 Sign in with Google", type="primary", use_container_width=True):
                st.login()

            # st.markdown("</div>", unsafe_allow_html=True)
        else:
            # User is logged in - show welcome message
            email = st.user.email
            token = generate_email_jwt(email)
            st.session_state["id_token"] = token

            st.markdown("<div class='login-section'>", unsafe_allow_html=True)
            st.success(f"✅ Welcome back, **{st.user.name}**!")
            st.info("🔄 Redirecting to your dashboard...")
            st.markdown("</div>", unsafe_allow_html=True)

            # Auto-redirect
            st.switch_page("pages/home.py")

        # Features section with improved layout
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title'>Why Choose Us?</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Feature highlights in columns
        feat_col1, feat_col2, feat_col3 = st.columns(3)

        with feat_col1:
            st.markdown("""
                <div class='feature-card'>
                    <div class='feature-icon'>📊</div>
                    <div class='feature-title'>Smart Analytics</div>
                    <div class='feature-text'>Visualize your spending patterns with interactive charts and detailed reports</div>
                </div>
            """, unsafe_allow_html=True)

        with feat_col2:
            st.markdown("""
                <div class='feature-card'>
                    <div class='feature-icon'>🎯</div>
                    <div class='feature-title'>Goal Tracking</div>
                    <div class='feature-text'>Set financial goals and track your progress with automated insights</div>
                </div>
            """, unsafe_allow_html=True)

        with feat_col3:
            st.markdown("""
                <div class='feature-card'>
                    <div class='feature-icon'>🔒</div>
                    <div class='feature-title'>Secure & Private</div>
                    <div class='feature-text'>Your data is encrypted and protected with enterprise-grade security</div>
                </div>
            """, unsafe_allow_html=True)

        # Additional benefits section
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Footer with better styling
        st.markdown("""
            <div class='footer'>
                <p>© 2025 Personal Finance Advisor. All rights reserved.</p>
                <p style='margin-top: 0.5rem; font-size: 0.85rem;'>Empowering your financial decisions, one insight at a time.</p>
            </div>
        """, unsafe_allow_html=True)


# Run the main function
if __name__ == "__main__":
    login()