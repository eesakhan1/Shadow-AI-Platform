import os # Add this at the top
import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
import random
import requests
import time

# --- 1. CONFIGURATION ---



# --- CONFIGURATION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
RESEND_FROM_EMAIL = "onboarding@resend.dev"

# Initialize
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- PAGE SETUP - ENTERPRISE GRADE ---
st.set_page_config(
    page_title="Shadow AI | Enterprise Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS - THE MILLION DOLLAR LOOK ---
st.markdown("""
    <style>
    .main {
        background: radial-gradient(circle at top left, #1e3a8a 0%, #0e1117 40%, #000000 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 55px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 255, 200, 0.2);
    }
    .login-card {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    .stat-card {
        background: rgba(0,0,0,0.3);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #00ffcc;
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
                    <h1 style="color:#00ffcc;">🛡️ Shadow AI</h1>
                    <p>Your verification code is:</p>
                    <h2 style="font-size:50px; letter-spacing:10px; color:#2563eb;">{code}</h2>
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
            email = st.text_input("📧 Email", key="login_email")
            password = st.text_input("🔒 Password", type="password", key="login_pass")
            
            if st.button("🚀 Authenticate", type="primary"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    code = str(random.randint(100000, 999999))
                    
                    send_verification_email(email, code)
                    
                    st.session_state.temp_code = code
                    st.session_state.temp_email = email
                    st.session_state.temp_pass = password
                    st.session_state.auth_stage = "verify"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Login Failed: {str(e)}")

            if st.session_state.auth_stage == "verify":
                user_code = st.text_input("Enter 6-Digit Code", max_chars=6)
                if st.button("✅ Verify"):
                    if user_code == st.session_state.temp_code:
                        st.session_state.user = res.user
                        st.session_state.user_id = res.user.id
                        st.session_state.auth_stage = "login"
                        st.rerun()
                    else:
                        st.error("Invalid Code")

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

# --- D
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

    # --- 🚀 ENTERPRISE DEPLOYMENT SECTION ---
    st.subheader("📦 Deployment Center")
    with st.expander("🔧 Install Extension", expanded=True):
        col1, col2 = st.columns([3,1])
        with col1:
            st.info("""
            Download your unique configuration file. 
            Place this file inside your extension folder to activate security policies.
            """)
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

    # --- METRICS ROW ---
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(label="🛡️ Active Shield", value="Online")
    with col_b:
        st.metric(label="🔒 Security Level", value="Maximum")
    with col_c:
        st.metric(label="📍 Region", value="Europe")

    # --- 1. LIVE LOGS ---
    st.divider()
    st.subheader("📋 Live Activity Logs")
    if st.button("🔄 Refresh Data"):
        st.rerun()
        
    try:
        if st.session_state.user_id:
            data = supabase.table("security_logs")\
                .select("*")\
                .eq("user_id", st.session_state.user_id)\
                .order("created_at", desc=True)\
                .execute()
                
            if data.data:
                df = pd.DataFrame(data.data)
                st.dataframe(df, use_container_width=True, height=300)
            else:
                st.info("No security events detected yet.")
    except Exception as e:
        st.warning(f"Could not load logs: {e}")

    # --- 2. RULE CREATOR ---
    st.divider()
    st.subheader("🎛️ Security Policies")
    
    col1, col2 = st.columns(2)
    with col1:
        secret_word = st.text_input("🔒 Sensitive Word / Phrase", placeholder="e.g. Project X, Budget 2025")
    with col2:
        replacement_label = st.text_input("🏷️ Replacement Label", placeholder="e.g. [CONFIDENTIAL]", value="[REDACTED]")

    if st.button("✅ Deploy Security Rule", type="primary"):
        if secret_word and replacement_label:
            try:
                supabase.table("company_secrets").insert({
                    "secret_word": secret_word,
                    "label": replacement_label,
                    "user_id": st.session_state.user_id
                }).execute()
                st.success(f"✅ Rule Active: '{secret_word}' will be blocked automatically.")
            except Exception as e:
                st.error(f"Failed to save rule: {e}")
        else:
            st.warning("⚠️ Please fill in both fields.")

# --- 3. ROUTING ---
if st.session_state.user is None:
    show_login()
else:
    show_dashboard()