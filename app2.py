import os
import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
import random
import requests
import time
import zipfile
from io import BytesIO
import string
import json
import urllib.parse

# --- CONFIGURATION ---
try:
    SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or st.secrets["SUPABASE_SERVICE_KEY"]
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or st.secrets["SUPABASE_ANON_KEY"]
    RESEND_API_KEY = os.getenv("RESEND_API_KEY") or st.secrets["RESEND_API_KEY"]
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL") or "security@shadowaisecurity.co.uk"
except Exception as e:
    st.error(f"Missing Secrets: {e}")
    st.stop()

ADMIN_EMAIL = "security.shadowai@gmail.com"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- LICENCE KEY VALIDATION ---
def is_licence_valid(licence_key: str) -> bool:
    if not licence_key:
        return False
    try:
        response = supabase.table("licences") \
                           .select("is_active, expires_at") \
                           .eq("licence_key", licence_key) \
                           .single()
        data = response.data
        if not data:
            return False
        if not data.get("is_active", False):
            return False
        expires_at = data.get("expires_at")
        if expires_at:
            expiry_dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry_dt < datetime.datetime.now(datetime.timezone.utc):
                return False
        return True
    except Exception as e:
        print(f"Licence check error: {e}")
        return False

# --- GENERATE LICENCE KEY ---
def generate_licence_key() -> str:
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SHADOW-{part1}-{part2}"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Shadow AI Security Limited | Data Protection & AI Security",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLACK & GOLD THEME ---
st.markdown("""
    <style>
    /* Base theme */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, Arial, sans-serif !important;
    }
    .stApp {
        background-color: #000000 !important;
        color: #FFD700 !important;
    }

    /* Color scheme - Black & Gold */
    :root {
        --primary: #FFD700;
        --primary-dark: #CCAC00;
        --primary-light: #222200;
        --success: #85BB65;
        --danger: #E63946;
        --neutral-100: #111111;
        --neutral-200: #222222;
        --neutral-300: #333333;
        --neutral-500: #999999;
        --neutral-800: #EEEEEE;
        --border: #444444;
        --shadow: 0 2px 10px rgba(255, 215, 0, 0.15);
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #FFD700 !important;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }
    h1 {
        font-size: 2.2rem;
    }
    h2 {
        font-size: 1.6rem;
    }
    h3 {
        font-size: 1.3rem;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 45px;
        font-size: 16px;
        font-weight: 500;
        border: 1px solid #FFD700;
        background: #FFD700;
        color: #000000 !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: #CCAC00;
        border-color: #CCAC00;
        color: #000000 !important;
    }
    .stButton>button.delete-btn {
        background: #E63946;
        border-color: #E63946;
        color: #FFFFFF !important;
    }
    .stButton>button.delete-btn:hover {
        background: #C22B37;
        border-color: #C22B37;
    }

    /* Cards & Containers */
    .login-card {
        background: #111111;
        padding: 2.5rem;
        border-radius: 6px;
        border: 1px solid #FFD700;
        box-shadow: var(--shadow);
        max-width: 480px;
        margin: 3rem auto;
    }
    .card {
        background: #111111;
        padding: 1.5rem;
        border-radius: 6px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        margin-bottom: 1.2rem;
    }

    /* Inputs */
    .stTextInput>div>div>input,
    .stPasswordInput>div>div>input {
        border: 1px solid #555555 !important;
        border-radius: 4px !important;
        background: #000000 !important;
        color: #FFD700 !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 15px !important;
    }
    .stTextInput>div>div>input:focus,
    .stPasswordInput>div>div>input:focus {
        border-color: #FFD700 !important;
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.2) !important;
    }
    .stTextInput label,
    .stPasswordInput label {
        color: #FFD700 !important;
        font-weight: 500 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background: #111111;
        border: 1px solid var(--border);
        border-radius: 4px 4px 0 0;
        color: #CCCCCC !important;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #222222;
        color: #FFD700 !important;
        border-color: #FFD700;
        border-bottom: 2px solid #FFD700;
    }

    /* Status messages */
    .stSuccess {
        background: #1A2A1E !important;
        color: #85BB65 !important;
        border: 1px solid #40604A !important;
        border-radius: 4px !important;
    }
    .stError {
        background: #2A1A1E !important;
        color: #E63946 !important;
        border: 1px solid #60404A !important;
        border-radius: 4px !important;
    }
    .stInfo {
        background: #222200 !important;
        color: #FFD700 !important;
        border: 1px solid #555500 !important;
        border-radius: 4px !important;
    }
    .stWarning {
        background: #2A2500 !important;
        color: #FFD700 !important;
        border: 1px solid #605500 !important;
        border-radius: 4px !important;
    }

    /* Compliance / Info badge */
    .info-badge {
        background: #222200;
        color: #FFD700;
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 13px;
        display: inline-block;
        margin: 0.5rem 0 1.2rem 0;
        border: 1px solid #444400;
    }

    /* Tables / Dataframes */
    .stDataFrame {
        border: 1px solid #444444;
        border-radius: 4px;
        overflow: hidden;
    }
    .stDataFrame table {
        border-collapse: collapse;
        width: 100%;
    }
    .stDataFrame th {
        background: #111111 !important;
        color: #FFD700 !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #444444 !important;
        padding: 0.8rem !important;
    }
    .stDataFrame td {
        color: #EEEEEE !important;
        border-bottom: 1px solid #333333 !important;
        padding: 0.7rem !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #111111 !important;
        border-right: 1px solid #444444;
        padding-top: 1rem;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #FFD700 !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #EEEEEE !important;
    }

    /* Links */
    a {
        color: #FFD700 !important;
        text-decoration: none;
        font-weight: 500;
    }
    a:hover {
        text-decoration: underline;
        color: #CCAC00 !important;
    }

    /* Code blocks */
    .stCodeBlock {
        background: #111111 !important;
        border: 1px solid #444444 !important;
        border-radius: 4px !important;
        color: #FFD700 !important;
    }

    /* Select boxes, dropdowns */
    .stSelectbox>div>div {
        background: #111111 !important;
        border: 1px solid #555555 !important;
        color: #FFD700 !important;
    }

    /* Logo container */
    .logo-container {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTENCE ---
def init_persistence():
    params = st.query_params
    if "uid" in params and "cid" in params and "email" in params:
        st.session_state.user = {"id": params["uid"], "email": params["email"]}
        st.session_state.user_id = params["uid"]
        st.session_state.company_id = params["cid"]
        st.session_state.auth_stage = "dashboard"
        return

    st.components.v1.html("""
    <script>
    const saved = localStorage.getItem('shadow_auth_v2');
    if (saved) {
        const data = JSON.parse(saved);
        const url = new URL(window.location);
        url.searchParams.set('uid', data.uid);
        url.searchParams.set('cid', data.cid);
        url.searchParams.set('email', data.email);
        window.history.replaceState({}, '', url);
        window.location.reload();
    }
    </script>
    """, height=0)

def save_auth(uid, cid, email):
    st.query_params["uid"] = uid
    st.query_params["cid"] = cid
    st.query_params["email"] = email
    auth_data = json.dumps({"uid": uid, "cid": cid, "email": email})
    st.components.v1.html(f"""
    <script>
    localStorage.setItem('shadow_auth_v2', `{auth_data}`);
    if (typeof chrome !== 'undefined' && chrome.storage) {{
        chrome.storage.local.set({{ "shadow_company_id": "{cid}" }});
    }}
    </script>
    """, height=0)

def clear_auth():
    st.query_params.clear()
    st.components.v1.html("""
    <script>
    localStorage.removeItem('shadow_auth_v2');
    if (typeof chrome !== 'undefined' && chrome.storage) {{
        chrome.storage.local.remove('shadow_company_id');
    }}
    </script>
    """, height=0)

# --- SESSION STATE ---
init_persistence()
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'company_id' not in st.session_state:
    st.session_state.company_id = None
if 'auth_stage' not in st.session_state:
    st.session_state.auth_stage = "login"
if 'temp_user_obj' not in st.session_state:
    st.session_state.temp_user_obj = None
if 'verification_code' not in st.session_state:
    st.session_state.verification_code = None

# --- EMAIL FUNCTIONS ---
def send_verification_email(to_email, code):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "Shadow AI Security Limited | Security Verification Code",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#000000; padding:30px; color:#FFD700; max-width:600px; border:1px solid #FFD700;">
                    <div style="background:#000000; padding:15px; border-bottom:1px solid #FFD700;">
                        <h1 style="color:#FFD700; margin:0;">Shadow AI Security Limited</h1>
                        <p style="color:#CCCCCC; margin:5px 0 0 0;">Data Protection & AI Security Solutions</p>
                    </div>
                    <div style="padding:20px; background:#111111; border-radius:4px; margin-top:15px;">
                        <p>Your verification code is:</p>
                        <h2 style="font-size:40px; letter-spacing:8px; color:#FFD700; margin:20px 0; text-align:center;">{code}</h2>
                        <p>Enter this code in your dashboard to continue.</p>
                        <p style="margin-top:30px; font-size:14px; color:#999;">Shadow AI Security Limited | Evergreen Assessment Registered | Ref: a0BPz0000GzZ65MAF20260528125015</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

def send_reset_email(to_email, reset_link):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "Shadow AI Security Limited | Reset Your Password",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#000000; padding:30px; color:#FFD700; max-width:600px; border:1px solid #FFD700;">
                    <div style="background:#000000; padding:15px; border-bottom:1px solid #FFD700;">
                        <h1 style="color:#FFD700; margin:0; font-size:20px; font-weight:normal;">Shadow AI Security Limited</h1>
                        <p style="color:#CCCCCC; margin:5px 0 0 0; font-size:14px;">Data Protection & AI Security Solutions</p>
                    </div>
                    <div style="padding:20px; background:#111111; border-radius:4px; margin-top:15px;">
                        <p style="font-size:16px; line-height:1.5;">You requested to reset your password for your Shadow AI Security Limited account.</p>
                        <p style="font-size:16px; line-height:1.5; margin:20px 0;">Click the button below to create a new password:</p>
                        <div style="text-align:center; margin:30px 0;">
                            <a href="{reset_link}" style="background:#FFD700; color:#000000; padding:12px 24px; border-radius:4px; text-decoration:none; font-weight:bold; font-size:16px; display:inline-block;">
                                Reset My Password
                            </a>
                        </div>
                        <p style="font-size:14px; color:#999; margin-top:30px;">This link is valid for <strong>60 minutes</strong>. If you did not request this change, please ignore this email or contact support immediately.</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

def send_licence_email(to_email, licence_key, org_name):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "Shadow AI Security Limited | Your Licence Key & Setup Instructions",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#000000; padding:30px; color:#FFD700; max-width:600px; border:1px solid #FFD700;">
                    <div style="background:#000000; padding:15px; border-bottom:1px solid #FFD700;">
                        <h1 style="color:#FFD700; margin:0;">Shadow AI Security Limited</h1>
                        <p style="color:#CCCCCC; margin:5px 0 0 0;">Data Protection & AI Security Solutions</p>
                    </div>
                    <div style="padding:20px; background:#111111; border-radius:4px; margin-top:15px;">
                        <p>Thank you for choosing Shadow AI Security Limited for <strong>{org_name}</strong>.</p>
                        <p>Your licence key to activate the extension is:</p>
                        <h2 style="font-size:24px; letter-spacing:4px; color:#FFD700; margin:20px 0; text-align:center; background:#000; padding:10px; border:1px solid #FFD700; border-radius:4px;">{licence_key}</h2>
                        <p><strong>Setup Steps:</strong></p>
                        <ol style="color:#EEEEEE;">
                            <li>Install the extension: <a href="https://chrome.google.com/webstore/detail/your-extension-id" style="color:#FFD700;">Chrome Web Store</a></li>
                            <li>Click the Shadow AI Security Limited icon in your toolbar</li>
                            <li>Enter the key above and click Activate</li>
                        </ol>
                        <p style="margin-top:30px; font-size:14px; color:#999;">Valid for 12 months | Support: security@shadowaisecurity.co.uk</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

# --- FORGOT PASSWORD ---
def show_forgot_password():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("Reset Your Password")
    st.markdown("Enter your registered work email — we will send you a secure reset link.")

    email = st.text_input("Official Work Email Address")

    if st.button("Send Reset Link"):
        if not email:
            st.warning("Please enter your email address")
        else:
            try:
                encoded_email = urllib.parse.quote(email.strip())
                reset_link = f"https://shadow-ai-platform.onrender.com/?mode=reset&email={encoded_email}"
                if send_reset_email(email, reset_link):
                    st.success("Reset link sent successfully!")
                    st.info("Email sent — check your inbox/spam")
                else:
                    st.error("Failed to send email — please try again")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("<br><p style='text-align:center;'><a href='/' style='color:#FFD700;'>← Back to Login</a></p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_reset_password(email):
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("Create New Password")
    st.markdown(f"Setting new password for: **{email}**")

    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password"):
        if new_password != confirm_password:
            st.error("Passwords do not match")
        elif len(new_password) < 8:
            st.warning("Password must be at least 8 characters")
        else:
            try:
                users = supabase.auth.admin.list_users()
                target_user = next((u for u in users if u.email == email), None)
                if not target_user:
                    st.error("Account not found")
                else:
                    supabase.auth.admin.update_user_by_id(target_user.id, {"password": new_password})
                    st.success("Password updated successfully! You can now log in.")
                    st.markdown("<p style='text-align:center; margin-top:20px;'><a href='/' style='color:#FFD700; font-weight:normal;'>← Go to Login</a></p>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIN SCREEN ---
def show_login():
    # Logo + Header
    st.markdown("""
    <div class="logo-container">
        <h1>Shadow AI Security Limited</h1>
        <p style="font-size: 18px; color: #CCCCCC;">Data Protection & AI Security Solutions</p>
        <div class="info-badge">Evergreen Assessment Registered | Ref: a0BPz0000GzZ65MAF20260528125015</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("Secure Access")
        tab1, tab2 = st.tabs(["Sign In", "Register"])
        
        with tab1:
            if st.session_state.auth_stage == "login":
                email = st.text_input("Official Work Email Address", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Login", type="primary"):
                    try:
                        res = auth_client.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.temp_user_obj = res.user
                        company_data = supabase.table("companies").select("id, max_devices").eq("email", email).execute()
                        if company_data.data:
                            st.session_state.company_id = company_data.data[0]["id"]
                            code = str(random.randint(100000, 999999))
                            st.session_state.verification_code = code
                            if send_verification_email(email, code):
                                st.session_state.auth_stage = "verify"
                                st.rerun()
                        else:
                            st.error("Account not found — please register first")
                    except Exception as e:
                        st.error(f"Access Denied: {str(e)}")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<p style="text-align:center;"><a href="/?page=forgot-password" style="color:#FFD700;">Forgot your password?</a></p>', unsafe_allow_html=True)
            elif st.session_state.auth_stage == "verify":
                st.info(f"Verification code sent to: **{st.session_state.temp_user_obj.email}**")
                user_code = st.text_input("Enter 6-Digit Security Code", max_chars=6)
                if st.button("Verify & Access Dashboard"):
                    if user_code == st.session_state.verification_code:
                        save_auth(st.session_state.temp_user_obj.id, st.session_state.company_id, st.session_state.temp_user_obj.email)
                        st.session_state.user = st.session_state.temp_user_obj
                        st.session_state.user_id = st.session_state.temp_user_obj.id
                        st.session_state.auth_stage = "dashboard"
                        st.success("Login Successful — Protection Active")
                        st.rerun()
                    else:
                        st.error("Invalid or expired code")
                if st.button("Back to Login"):
                    st.session_state.auth_stage = "login"
                    st.rerun()

        with tab2:
            st.warning("For paying customers only — access is granted after registration & verification")
            new_email = st.text_input("Official Work Email", key="reg_email")
            new_pass = st.text_input("Create Password", type="password", key="reg_pass")
            company_name = st.text_input("Organisation Name / Trust Name")
            max_devices = st.number_input("Number of Devices Licensed", min_value=1, max_value=10000, value=100, step=1)
            if st.button("Create Account"):
                try:
                    res = auth_client.auth.sign_up({"email": new_email, "password": new_pass})
                    company_id = "org_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    licence_key = generate_licence_key()
                    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()
                    supabase.table("licences").insert({
                        "licence_key": licence_key,
                        "organisation_name": company_name,
                        "contact_email": new_email,
                        "is_active": True,
                        "expires_at": expiry_date
                    }).execute()
                    supabase.table("companies").insert({
                        "id": company_id,
                        "name": company_name,
                        "email": new_email,
                        "is_active": True,
                        "max_devices": max_devices
                    }).execute()
                    if send_licence_email(new_email, licence_key, company_name):
                        st.success("ACCOUNT CREATED SUCCESSFULLY")
                        st.info("Licence key and setup instructions have been emailed to you")
                    else:
                        st.warning("Account created, but email failed — key: " + licence_key)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- GET SECURITY LOGS ---
@st.cache_data(ttl=0, show_spinner=False)
def get_security_logs(company_id):
    id_list = [company_id]
    if len(company_id) > 1:
        id_list.append(company_id[:-1])
    data = supabase.table("security_logs") \
        .select("*") \
        .in_("company_id", id_list) \
        .order("created_at", desc=True) \
        .execute()
    return data.data

# --- DASHBOARD ---
def show_dashboard():
    try:
        company_data = supabase.table("companies").select("is_active, name, email, max_devices").eq("id", st.session_state.company_id).execute()
        is_active = True
        org_name = company_data.data[0].get("name", "Your Organisation") if company_data.data else "Your Organisation"
        user_email = company_data.data[0].get("email", "") if company_data.data else ""
        max_devices = company_data.data[0].get("max_devices", 100) if company_data.data else 100
    except:
        is_active = True
        org_name = "Your Organisation"
        user_email = ""
        max_devices = 100

    try:
        id_list = [st.session_state.company_id]
        if len(st.session_state.company_id) > 1:
            id_list.append(st.session_state.company_id[:-1])
        dev_count = supabase.table("active_protection_devices").select("id", count="exact").in_("company_id", id_list).execute()
        active_devices = dev_count.count or 0
    except:
        active_devices = 0

    # Sidebar
    st.sidebar.markdown("""
    <div style="text-align:center; margin-bottom:1rem;">
        <h2>Shadow AI Security Limited</h2>
        <p style="font-size:13px; color:#CCCCCC;">Data Protection & AI Security</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(f"**{org_name}**")
    st.sidebar.markdown(f"**Reference: `{st.session_state.company_id}`**")
    st.sidebar.markdown(f"Devices: {active_devices} / {max_devices}")
    
    if is_active:
        st.sidebar.success("License: ACTIVE")
    else:
        st.sidebar.error("License: INACTIVE")

    if st.sidebar.button("Logout"):
        clear_auth()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if user_email == ADMIN_EMAIL:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Deployment", "Licence Keys", "Security Logs", "Active Devices", "Admin Users"])
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["Deployment", "Your Licence Key", "Security Logs", "Active Devices"])

    with tab1:
        st.title("Security Command Center")
        st.markdown('<div class="info-badge">Secure Data Protection & Auditing Enabled</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Deploy Protection Software")
        st.markdown("""
        **Official Chrome Web Store Extension**  
        No developer mode required — safe, verified, and automatically updated.
        **[Install from Chrome Web Store](https://chrome.google.com/webstore/detail/your-extension-id)**  
        *Works on Chrome, Edge, and Brave — fully secure and compliant*
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Custom Security Rules")
        st.markdown("*Add words, codes, or identifiers specific to your organisation*")
        col1, col2 = st.columns(2)
        with col1:
            secret_word = st.text_input("Sensitive Term / Phrase")
        with col2:
            replacement_label = st.text_input("Redaction Label", value="[ORGANISATION RESTRICTED]")
        if st.button("Deploy Rule Immediately"):
            if secret_word:
                try:
                    supabase.table("company_secrets").insert({
                        "secret_word": secret_word,
                        "label": replacement_label,
                        "company_id": st.session_state.company_id
                    }).execute()
                    st.success("Rule added — protection updated across all devices")
                except Exception as e:
                    st.error(f"Error saving rule: {str(e)}")

    with tab2:
        st.title("Your Licence Key")
        st.markdown('<div class="info-badge">Required to activate the extension</div>', unsafe_allow_html=True)
        st.markdown("---")
        try:
            licence_data = supabase.table("licences") \
                .select("licence_key, is_active, expires_at, created_at") \
                .eq("contact_email", user_email) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            if licence_data.data:
                lic = licence_data.data[0]
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("Licence Key")
                    st.code(lic['licence_key'], language="text")
                with col_b:
                    if lic['is_active']:
                        st.success("STATUS: ACTIVE")
                    else:
                        st.error("STATUS: INACTIVE / EXPIRED")
                    exp_date = lic['expires_at'][:10] if lic['expires_at'] else "Lifetime"
                    st.info(f"Expires: {exp_date}")
                st.markdown("---")
                st.subheader("How to Activate")
                st.markdown("""
                1. Install the extension from the Chrome Web Store
                2. Click the Shadow AI Security Limited icon in your browser toolbar
                3. Paste this key into the activation box
                4. Click Activate — protection starts immediately
                """)
                if user_email == ADMIN_EMAIL:
                    st.markdown("---")
                    st.subheader("Admin Actions")
                    if st.button("Revoke This Key"):
                        supabase.table("licences").update({"is_active": False}).eq("licence_key", lic['licence_key']).execute()
                        st.warning("Key revoked — extension will stop working immediately")
                        st.rerun()
                    if st.button("Renew for 12 Months"):
                        new_expiry = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()
                        supabase.table("licences").update({"is_active": True, "expires_at": new_expiry}).eq("licence_key", lic['licence_key']).execute()
                        st.success("Licence renewed — 12 months added")
                        st.rerun()
            else:
                st.info("No licence key found — please contact support")
        except Exception as e:
            st.error(f"Error loading licence: {str(e)}")

    with tab3:
        st.title("Security Audit Logs")
        st.markdown('<div class="info-badge">Full activity logging and compliance tracking</div>', unsafe_allow_html=True)
        st.markdown("---")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Refresh Now"):
                st.cache_data.clear()
                st.rerun()
        with col2:
            st.info("Auto-refreshing every 30 seconds...")

        if 'last_refresh' not in st.session_state or (datetime.datetime.now() - st.session_state.last_refresh).seconds > 30:
            st.session_state.last_refresh = datetime.datetime.now()
            st.cache_data.clear()
            st.rerun()

        logs = get_security_logs(st.session_state.company_id)
        
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.info("No security events recorded — protection is active and monitoring.")

    with tab4:
        st.title("Active Protected Devices")
        st.markdown('<div class="info-badge">Only devices with extension installed & running</div>', unsafe_allow_html=True)
        st.markdown("---")
        try:
            id_list = [st.session_state.company_id]
            if len(st.session_state.company_id) > 1:
                id_list.append(st.session_state.company_id[:-1])
            devices = supabase.table("active_protection_devices").select("*").in_("company_id", id_list).order("last_heartbeat", desc=True).execute()
            if devices.data:
                st.write(f"**{len(devices.data)} active device(s) out of {max_devices} paid limit**")
                for dev in devices.data:
                    cols = st.columns([3,2,1])
                    with cols[0]:
                        st.markdown(f"**{dev['device_name']}**")
                    with cols[1]:
                        st.caption(f"Last seen: {dev['last_heartbeat'][:16]}")
                    with cols[2]:
                        if st.button("Remove", key=dev['id'], help="Revoke protection from this device"):
                            supabase.table("active_protection_devices").delete().eq("id", dev['id']).execute()
                            st.success("Device removed — protection stopped")
                            st.rerun()
            else:
                st.info("No active protected devices — install from Chrome Web Store to start.")
        except Exception as e:
            st.error(f"Error loading devices: {str(e)}")

    if user_email == ADMIN_EMAIL:
        with tab5:
            st.title("Registered Companies & Users")
            st.markdown('<div class="info-badge">Admin Access — View and manage all accounts</div>', unsafe_allow_html=True)
            st.markdown("---")
            try:
                all_companies = supabase.table("companies").select("id, name, email, is_active, max_devices").execute()
                if all_companies.data:
                    df = pd.DataFrame(all_companies.data)
                    st.subheader(f"Total Registered: {len(all_companies.data)}")
                    st.dataframe(df, use_container_width=True, column_config={
                        "id": "Company ID",
                        "name": "Organisation Name",
                        "email": "Contact Email",
                        "is_active": "Active Status",
                        "max_devices": "Licensed Devices"
                    })
                    st.markdown("---")
                    st.subheader("Update License Limit")
                    company_options = {f"{row['name']} ({row['email']})": row['id'] for row in all_companies.data}
                    selected_label = st.selectbox("Select company:", list(company_options.keys()))
                    new_limit = st.number_input("New Device Limit", min_value=1, max_value=50000, value=100)
                    if st.button("UPDATE LIMIT"):
                        selected_id = company_options[selected_label]
                        supabase.table("companies").update({"max_devices": new_limit}).eq("id", selected_id).execute()
                        st.success("Limit updated — applies instantly to all devices")
                        st.rerun()
                    st.markdown("---")
                    st.subheader("Remove Unwanted Account")
                    selected_label_del = st.selectbox("Select account to remove:", list(company_options.keys()), key="del")
                    if st.button("DELETE ACCOUNT", type="primary", help="This will permanently remove the company and all its data"):
                        selected_id = company_options[selected_label_del]
                        try:
                            supabase.table("security_logs").delete().eq("company_id", selected_id).execute()
                            supabase.table("company_secrets").delete().eq("company_id", selected_id).execute()
                            supabase.table("active_protection_devices").delete().eq("company_id", selected_id).execute()
                            supabase.table("licences").delete().eq("contact_email", next(r['email'] for r in all_companies.data if r['id'] == selected_id)).execute()
                            supabase.table("companies").delete().eq("id", selected_id).execute()
                            try:
                                selected_email = next(row['email'] for row in all_companies.data if row['id'] == selected_id)
                                supabase.auth.admin.delete_user(selected_email)
                            except:
                                pass
                            st.success("Account and all associated data have been removed successfully")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error deleting account: {str(e)}")
                
                else:
                    st.info("No companies have registered yet.")

            except Exception as e:
                st.error(f"Error loading registered users: {str(e)}")

# --- ROUTING ---
def main():
    params = st.query_params
    page = params.get("page", "")
    mode = params.get("mode", "")
    reset_email = params.get("email", "")

    if page == "forgot-password":
        show_forgot_password()
        return
    if mode == "reset" and reset_email:
        from urllib.parse import unquote
        decoded_email = unquote(reset_email)
        show_reset_password(decoded_email)
        return
    if st.session_state.user is None or st.session_state.auth_stage in ["login", "verify"]:
        show_login()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()