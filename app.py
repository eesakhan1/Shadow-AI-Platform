import os
import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
import random
import requests
import time

# --- CONFIGURATION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
RESEND_FROM_EMAIL = "onboarding@resend.dev"

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Shadow AI | Enterprise Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS - LUXURY EDITION ---
st.markdown("""
    <style>
    .main {
        background: radial-gradient(circle at top left, #1a1a2e 0%, #000000 50%, #000000 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 55px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        transition: all 0.4s ease;
        background: linear-gradient(135deg, #d4af37 0%, #f0e68c 50%, #d4af37 100%);
        color: #000 !important;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 35px rgba(212, 175, 55, 0.8);
    }
    .login-card {
        background-color: rgba(10, 10, 25, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 15px;
        border: 1px solid rgba(212, 175, 55, 0.3);
        box-shadow: 0 10px 50px rgba(0,0,0,0.7);
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown p {
        color: #f0e68c !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stTextInput input, .stTextInput label {
        color: #e0e0e0 !important;
    }
    .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #d4af37 !important;
        border: 1px solid rgba(212, 175, 55, 0.2);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #d4af37 0%, #f0e68c 100%);
        color: #000000 !important;
        font-weight: bold;
    }
    .stInfo {
        background-color: rgba(212, 175, 55, 0.1) !important;
        color: #f0e68c !important;
        border: 1px solid #d4af37 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'auth_stage' not in st.session_state:
    st.session_state.auth_stage = "login"
if 'temp_user_obj' not in st.session_state:
    st.session_state.temp_user_obj = None

# --- EMAIL FUNCTION ---
def send_verification_email(to_email, code):
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "🔐 Shadow AI Security Code",
                "html": f"""
                <div style="font-family: 'Arial', sans-serif; background:#0a0a0a; padding:30px; color:white;">
                    <h1 style="color:#d4af37;">🛡️ Shadow AI</h1>
                    <p>Your verification code is:</p>
                    <h2 style="font-size:50px; letter-spacing:10px; color:#f0e68c;">{code}</h2>
                    <p>Enter this to access your security dashboard.</p>
                </div>
                """
            }
        )
        return True
    except:
        return False

# --- LOGIN SCREEN ---
def show_login():
    st.title("🛡️ Shadow AI Enterprise")
    st.markdown("#### *Global Data Protection Platform*")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("🔐 Secure Access")
        
        tab1, tab2 = st.tabs(["🔑 Sign In", "🆕 Register"])
        
        with tab1:
            if st.session_state.auth_stage == "login":
                email = st.text_input("📧 Email", key="login_email")
                password = st.text_input("🔒 Password", type="password", key="login_pass")
                
                if st.button("🚀 Authenticate", type="primary"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.temp_user_obj = res.user 
                        
                        code = str(random.randint(100000, 999999))
                        send_verification_email(email, code)
                        
                        st.session_state.temp_code = code
                        st.session_state.temp_email = email
                        st.session_state.auth_stage = "verify"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Login Failed: {str(e)}")

            elif st.session_state.auth_stage == "verify":
                st.info(f"🔢 Code sent to {st.session_state.temp_email}")
                user_code = st.text_input("Enter 6-Digit Code", max_chars=6)
                
                if st.button("✅ Verify"):
                    if user_code == st.session_state.temp_code:
                        st.session_state.user = st.session_state.temp_user_obj
                        st.session_state.user_id = st.session_state.temp_user_obj.id
                        st.session_state.auth_stage = "login"
                        st.rerun()
                    else:
                        st.error("Invalid Code")
                
                if st.button("🔙 Back"):
                    st.session_state.auth_stage = "login"
                    st.rerun()

        with tab2:
            new_email = st.text_input("📧 Work Email")
            new_pass = st.text_input("🔒 Password", type="password")
            company = st.text_input("🏢 Company Name")
            if st.button("✅ Create Account"):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_pass})
                    st.success("✅ Account Created! Please sign in.")
                except Exception as e:
                    st.error(str(e))
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD FUNCTION ---
def show_dashboard():
    # --- SIDEBAR ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/809/809934.png", width=80)
    st.sidebar.title("🛡️ Shadow AI")
    st.sidebar.markdown(f"**👤 {st.session_state.user.email}**")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.user_id = None
        st.rerun()

    # --- MAIN DASHBOARD ---
    st.title("🛡️ Security Command Center")
    st.markdown("##### *Real-time Protection & Policy Management*")
    st.markdown("---")

    # --- DEPLOYMENT SECTION ---
    st.subheader("📦 Deployment Center")
    with st.expander("🔧 Install Extension", expanded=True):
        col1, col2 = st.columns([3,1])
        with col1:
            st.info("Download your unique config.js. Place it in your extension folder.")
        with col2:
            config_content = f"""const SHADOW_AI_CONFIG = {{
            supabaseUrl: "{SUPABASE_URL}",
            supabaseKey: "{SUPABASE_SERVICE_KEY}",
            userId: "{st.session_state.user_id}" 
            }};"""
            
            st.download_button(
                label="⬇️ Download Config",
                data=config_content,
                file_name="config.js",
                mime="text/javascript",
                type="primary"
            )

    # --- LIVE LOGS ---
    st.divider()
    st.subheader("📋 Live Activity Logs")
    try:
        data = supabase.table("security_logs").select("*").eq("user_id", st.session_state.user_id).order("created_at", desc=True).execute()
        if data.data:
            st.dataframe(pd.DataFrame(data.data), use_container_width=True)
        else:
            st.info("No events detected.")
    except Exception as e:
        st.error(f"Error loading logs: {e}")

    # --- RULE CREATOR ---
    st.divider()
    st.subheader("🎛️ Security Policies")
    col1, col2 = st.columns(2)
    with col1:
        secret_word = st.text_input("🔒 Sensitive Word")
    with col2:
        replacement_label = st.text_input("🏷️ Label", value="[REDACTED]")

    if st.button("✅ Deploy Rule"):
        if secret_word:
            supabase.table("company_secrets").insert({
                "secret_word": secret_word,
                "label": replacement_label,
                "user_id": st.session_state.user_id
            }).execute()
            st.success("Rule Active!")

# --- ROUTING ---
if st.session_state.user is None:
    show_login()
else:
    show_dashboard()