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
    # ✅ Works both locally and on Render
    SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or st.secrets["SUPABASE_SERVICE_KEY"]
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or st.secrets["SUPABASE_ANON_KEY"]
    RESEND_API_KEY = os.getenv("RESEND_API_KEY") or st.secrets["RESEND_API_KEY"]
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL") or "security@shadowaisecurity.co.uk"
except Exception as e:
    st.error(f"❌ Missing Secrets: {e}")
    st.stop()

ADMIN_EMAIL = "security.shadowai@gmail.com"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- ✅ NEW: LICENCE KEY VALIDATION FUNCTION ---
def is_licence_valid(licence_key: str) -> bool:
    """Check if licence key exists, is active, and not expired"""
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
        # Check active status
        if not data.get("is_active", False):
            return False
        # Check expiry date
        expires_at = data.get("expires_at")
        if expires_at:
            expiry_dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry_dt < datetime.datetime.now(datetime.timezone.utc):
                return False
        return True
    except Exception as e:
        print(f"Licence check error: {e}")
        return False

# --- ✅ NEW: GENERATE LICENCE KEY FUNCTION ---
def generate_licence_key() -> str:
    """Generate unique licence key in format SHADOW-XXXX-XXXX"""
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SHADOW-{part1}-{part2}"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Shadow AI | NHS Compliant Data Protection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS — NHS STANDARD DARK THEME ---
st.markdown("""
    <style>
    .main {
        background: #0A0F1F;
        color: #FFFFFF;
        font-family: Arial, Helvetica, sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 55px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
        background: #005EB8;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0,94,184,0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background: #003087;
        box-shadow: 0 4px 12px rgba(0,48,135,0.5);
        transform: translateY(-1px);
    }
    .login-card {
        background-color: rgba(20, 30, 60, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 8px;
        border: 2px solid #005EB8;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        max-width: 550px;
        margin: 2rem auto;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-family: Arial, Helvetica, sans-serif;
        font-weight: bold;
    }
    .stMarkdown p {
        color: #E0E0E0 !important;
        font-size: 16px;
    }
    .stTextInput input, .stTextInput label {
        color: #FFFFFF !important;
    }
    .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid #005EB8;
        border-radius: 4px;
        color: #FFFFFF !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        color: #B0C4DE !important;
        border: 1px solid #003087;
    }
    .stTabs [aria-selected="true"] {
        background: #005EB8;
        color: #FFFFFF !important;
        font-weight: bold;
    }
    .stSuccess {
        background-color: rgba(0, 164, 153, 0.15) !important;
        color: #00A499 !important;
        border: 1px solid #00A499 !important;
    }
    .stError {
        background-color: rgba(218, 41, 28, 0.15) !important;
        color: #DA291C !important;
        border: 1px solid #DA291C !important;
    }
    .stInfo {
        background-color: rgba(0, 94, 184, 0.15) !important;
        color: #00A499 !important;
        border: 1px solid #005EB8 !important;
    }
    .compliance-badge {
        background: #00A499;
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
        margin: 8px 0;
    }
    .delete-btn {
        background-color: #DA291C !important;
        color: white !important;
    }
    .delete-btn:hover {
        background-color: #9E1A12 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- ✅ REFRESH-PROOF PERSISTENCE ---
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
                "subject": "🔐 Shadow AI | Security Verification Code",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#0A0F1F; padding:30px; color:white; max-width:600px;">
                    <div style="background:#003087; padding:15px; border-radius:4px;">
                        <h1 style="color:white; margin:0;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE; margin:5px 0 0 0;">NHS Compliant Data Protection</p>
                    </div>
                    <div style="padding:20px; background:#141E3C; border-radius:4px; margin-top:15px;">
                        <p>Your verification code is:</p>
                        <h2 style="font-size:50px; letter-spacing:10px; color:#00A499; margin:20px 0;">{code}</h2>
                        <p>Enter this code in your dashboard to continue.</p>
                        <p style="margin-top:30px; font-size:14px; color:#888;">Shadow AI is registered on the NHS Evergreen Supplier Assessment | Ref: a0BPz0000GzZ65MAF20260528125015</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Email Error: {e}")
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
                "subject": "🔐 Shadow AI | Reset Your Password",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#0A0F1F; padding:30px; color:white; max-width:600px;">
                    <div style="background:#003087; padding:15px; border-radius:4px;">
                        <h1 style="color:white; margin:0; font-size:24px; font-weight:bold;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE; margin:5px 0 0 0; font-size:14px;">NHS Compliant Data Protection</p>
                    </div>
                    <div style="padding:20px; background:#141E3C; border-radius:4px; margin-top:15px;">
                        <p style="font-size:16px; line-height:1.5;">You requested to reset your password for your Shadow AI account.</p>
                        <p style="font-size:16px; line-height:1.5; margin:20px 0;">Click the button below to create a new password:</p>
                        <div style="text-align:center; margin:30px 0;">
                            <a href="{reset_link}" style="background:#00A499; color:#ffffff; padding:14px 28px; border-radius:4px; text-decoration:none; font-weight:bold; font-size:16px; display:inline-block;">
                                Reset My Password
                            </a>
                        </div>
                        <p style="font-size:14px; color:#B0C4DE; margin-top:30px;">This link is valid for <strong>60 minutes</strong>. If you did not request this change, please ignore this email or contact support immediately.</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Email Error: {e}")
        return False

# --- ✅ NEW: SEND LICENCE KEY EMAIL ---
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
                "subject": "🔑 Shadow AI | Your Licence Key & Setup Instructions",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#0A0F1F; padding:30px; color:white; max-width:600px;">
                    <div style="background:#003087; padding:15px; border-radius:4px;">
                        <h1 style="color:white; margin:0;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE; margin:5px 0 0 0;">NHS Compliant Data Protection</p>
                    </div>
                    <div style="padding:20px; background:#141E3C; border-radius:4px; margin-top:15px;">
                        <p>Thank you for choosing Shadow AI for <strong>{org_name}</strong>.</p>
                        <p>Your licence key to activate the extension is:</p>
                        <h2 style="font-size:32px; letter-spacing:5px; color:#00A499; margin:20px 0; text-align:center;">{licence_key}</h2>
                        <p><strong>Setup Steps:</strong></p>
                        <ol>
                            <li>Install the extension: <a href="https://chrome.google.com/webstore/detail/your-extension-id" style="color:#00A499;">Chrome Web Store</a></li>
                            <li>Click the Shadow AI icon in your toolbar</li>
                            <li>Enter the key above and click Activate</li>
                        </ol>
                        <p style="margin-top:30px; font-size:14px; color:#888;">Valid for 12 months | Support: security@shadowaisecurity.co.uk</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Email Error: {e}")
        return False

# --- FORGOT PASSWORD ---
def show_forgot_password():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("🔑 Reset Your Password")
    st.markdown("Enter your registered work email — we’ll send you a secure reset link.")

    email = st.text_input("📧 Official Work Email Address")

    if st.button("📩 Send Reset Link"):
        if not email:
            st.warning("⚠️ Please enter your email address")
        else:
            try:
                encoded_email = urllib.parse.quote(email.strip())
                reset_link = f"https://shadow-ai-platform.onrender.com/?mode=reset&email={encoded_email}"

                if send_reset_email(email, reset_link):
                    st.success("✅ Reset link sent successfully!")
                    st.info("📧 Email sent — check your inbox/spam")
                else:
                    st.error("❌ Failed to send email — please try again")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown("<br><p style='text-align:center;'><a href='/' style='color:#4da6ff;'>← Back to Login</a></p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_reset_password(email):
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("🔑 Create New Password")
    st.markdown(f"Setting new password for: **{email}**")

    new_password = st.text_input("🔒 New Password", type="password")
    confirm_password = st.text_input("🔒 Confirm New Password", type="password")

    if st.button("✅ Update Password"):
        if new_password != confirm_password:
            st.error("❌ Passwords do not match")
        elif len(new_password) < 8:
            st.warning("⚠️ Password must be at least 8 characters")
        else:
            try:
                users = supabase.auth.admin.list_users()
                target_user = next((u for u in users if u.email == email), None)
                if not target_user:
                    st.error("❌ Account not found")
                else:
                    supabase.auth.admin.update_user_by_id(target_user.id, {"password": new_password})
                    st.success("✅ Password updated successfully! You can now log in.")
                    st.markdown("<p style='text-align:center; margin-top:20px;'><a href='/' style='color:#4da6ff; font-weight:bold;'>← Go to Login</a></p>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIN SCREEN ---
def show_login():
    st.title("🛡️ Shadow AI")
    st.markdown("#### *NHS Compliant Data Protection & AI Security*")
    st.markdown('<div class="compliance-badge">✅ Evergreen Assessment Registered | Ref: a0BPz0000GzZ65MAF20260528125015</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("🔐 Secure Access")

        tab1, tab2 = st.tabs(["🔑 Sign In", "🆕 Register"])
        
        with tab1:
            if st.session_state.auth_stage == "login":
                email = st.text_input("📧 Official Work Email Address", key="login_email")
                password = st.text_input("🔒 Password", type="password", key="login_pass")
                
                if st.button("🚀 Login", type="primary"):
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
                            st.error("❌ Account not found — please register first")
                            
                    except Exception as e:
                        st.error(f"❌ Access Denied: {str(e)}")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<p style="text-align:center;"><a href="/?page=forgot-password" style="color:#4da6ff;">🔑 Forgot your password?</a></p>', unsafe_allow_html=True)

            elif st.session_state.auth_stage == "verify":
                st.info(f"🔢 Verification code sent to: **{st.session_state.temp_user_obj.email}**")
                user_code = st.text_input("Enter 6-Digit Security Code", max_chars=6)
                
                if st.button("✅ Verify & Access Dashboard"):
                    if user_code == st.session_state.verification_code:
                        save_auth(
                            st.session_state.temp_user_obj.id,
                            st.session_state.company_id,
                            st.session_state.temp_user_obj.email
                        )
                        st.session_state.user = st.session_state.temp_user_obj
                        st.session_state.user_id = st.session_state.temp_user_obj.id
                        st.session_state.auth_stage = "dashboard"
                        st.success("✅ Login Successful — Protection Active")
                        st.rerun()
                    else:
                        st.error("❌ Invalid or expired code")
                
                if st.button("🔙 Back to Login"):
                    st.session_state.auth_stage = "login"
                    st.rerun()

        with tab2:
            st.warning("⚠️ For paying customers only — access is granted after registration & verification")
            new_email = st.text_input("📧 Official Work Email", key="reg_email")
            new_pass = st.text_input("🔒 Create Password", type="password", key="reg_pass")
            company_name = st.text_input("🏢 Organisation Name / Trust Name")
            max_devices = st.number_input("📱 Number of Devices Licensed", min_value=1, max_value=10000, value=100, step=1)
            
            if st.button("✅ Create Account"):
                try:
                    res = auth_client.auth.sign_up({"email": new_email, "password": new_pass})
                    company_id = "org_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    
                    # ✅ NEW: Generate licence key on registration
                    licence_key = generate_licence_key()
                    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()
                    
                    # ✅ NEW: Insert into licences table
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
                    
                    # ✅ NEW: Send licence key to customer
                    if send_licence_email(new_email, licence_key, company_name):
                        st.success("✅ ACCOUNT CREATED SUCCESSFULLY")
                        st.info("📧 Licence key and setup instructions have been emailed to you")
                    else:
                        st.warning("⚠️ Account created, but email failed — key: " + licence_key)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD FUNCTION ---
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
        dev_count = supabase.table("active_protection_devices").select("id", count="exact").eq("company_id", st.session_state.company_id).execute()
        active_devices = dev_count.count or 0
    except:
        active_devices = 0

    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/809/809934.png", width=80)
    st.sidebar.title("🛡️ Shadow AI")
    st.sidebar.markdown(f"**🏢 {org_name}**")
    st.sidebar.markdown(f"**Reference: `{st.session_state.company_id}`**")
    st.sidebar.markdown(f"📊 Devices: {active_devices} / {max_devices}")
    
    if is_active:
        st.sidebar.success("✅ License: ACTIVE | COMPLIANT")
    else:
        st.sidebar.error("❌ License: PENDING")

    if st.sidebar.button("🚪 Logout"):
        clear_auth()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if user_email == ADMIN_EMAIL:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 Deployment", "🔑 Licence Keys", "📋 Security Logs", "📱 Active Devices", "👤 Admin Users"])
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📦 Deployment", "🔑 Your Licence Key", "📋 Security Logs", "📱 Active Devices"])

    with tab1:
        st.title("🛡️ Security Command Center")
        st.markdown('<div class="compliance-badge">✅ NHS Information Governance Compliant | Audit Logging Enabled</div>', unsafe_allow_html=True)
        st.markdown("---")

        st.subheader("📦 Deploy Protection Software")
        st.markdown("""
        **✅ Official Chrome Web Store Extension**  
        No developer mode required — safe, verified, and automatically updated.
        
        👉 **[Install from Chrome Web Store](https://chrome.google.com/webstore/detail/your-extension-id)**  
        *Works on Chrome, Edge, and Brave — fully compliant and secure*
        """, unsafe_allow_html=True)

        st.markdown("---")
        
        st.subheader("🎛️ Custom Security Rules")
        st.markdown("*Add words, codes, or identifiers specific to your organisation (e.g. local patient codes, project names)*")
        col1, col2 = st.columns(2)
        with col1:
            secret_word = st.text_input("🔒 Sensitive Term / Phrase")
        with col2:
            replacement_label = st.text_input("🏷️ Redaction Label", value="[ORGANISATION RESTRICTED]")

        if st.button("✅ Deploy Rule Immediately"):
            if secret_word:
                try:
                    supabase.table("company_secrets").insert({
                        "secret_word": secret_word,
                        "label": replacement_label,
                        "company_id": st.session_state.company_id
                    }).execute()
                    st.success("✅ Rule added — protection updated across all devices")
                except Exception as e:
                    st.error(f"Error saving rule: {str(e)}")

    # --- ✅ NEW: LICENCE KEY TAB FOR ALL USERS ---
    with tab2:
        st.title("🔑 Your Licence Key")
        st.markdown('<div class="compliance-badge">✅ Required to activate the extension</div>', unsafe_allow_html=True)
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
                    st.subheader("🔑 Licence Key")
                    st.code(lic['licence_key'], language="text")
                with col_b:
                    if lic['is_active']:
                        st.success("✅ STATUS: ACTIVE")
                    else:
                        st.error("❌ STATUS: INACTIVE / EXPIRED")
                    exp_date = lic['expires_at'][:10] if lic['expires_at'] else "Lifetime"
                    st.info(f"📅 Expires: {exp_date}")

                st.markdown("---")
                st.subheader("📋 How to Activate")
                st.markdown("""
                1. Install the extension from the Chrome Web Store
                2. Click the Shadow AI icon in your browser toolbar
                3. Paste this key into the activation box
                4. Click **Activate** — protection starts immediately
                """)

                # ✅ NEW: Admin can revoke/renew
                if user_email == ADMIN_EMAIL:
                    st.markdown("---")
                    st.subheader("⚙️ Admin Actions")
                    if st.button("❌ Revoke This Key"):
                        supabase.table("licences").update({"is_active": False}).eq("licence_key", lic['licence_key']).execute()
                        st.warning("✅ Key revoked — extension will stop working immediately")
                        st.rerun()
                    if st.button("✅ Renew for 12 Months"):
                        new_expiry = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()
                        supabase.table("licences").update({"is_active": True, "expires_at": new_expiry}).eq("licence_key", lic['licence_key']).execute()
                        st.success("✅ Licence renewed — 12 months added")
                        st.rerun()
            else:
                st.info("No licence key found — please contact support")

        except Exception as e:
            st.error(f"Error loading licence: {str(e)}")

    with tab3:
        st.title("📋 Security Audit Logs")
        st.markdown('<div class="compliance-badge">✅ NHS Information Governance Compliant | Audit Logging Enabled</div>', unsafe_allow_html=True)
        st.markdown("---")

        # ✅ ADDED: Refresh Button + Auto-Refresh every 30s
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Refresh Now"):
                st.rerun()
        with col2:
            st.info("⏱️ Auto-refreshing every 30 seconds...")

        # Auto-refresh timer
        import time
        time.sleep(30)
        st.rerun()
        
        try:
            # ✅ FIXED: Only filter by company_id (master ID) — NO OR MISMATCHES
            data = supabase.table("security_logs") \
                .select("*") \
                .eq("company_id", st.session_state.company_id) \
                .order("created_at", desc=True) \
                .execute()
                
            if data.data:
                st.dataframe(pd.DataFrame(data.data), use_container_width=True)
            else:
                st.info("No security events recorded — protection is active and monitoring.")
        except Exception as e:
            st.error(f"Error loading logs: {str(e)}")

    with tab4:
        st.title("📱 Active Protected Devices")
        st.markdown('<div class="compliance-badge">✅ Only devices with extension installed & running</div>', unsafe_allow_html=True)
        st.markdown("---")

        try:
            devices = supabase.table("active_protection_devices").select("*").eq("company_id", st.session_state.company_id).order("last_heartbeat", desc=True).execute()
            
            if devices.data:
                st.write(f"**{len(devices.data)} active device(s) out of {max_devices} paid limit**")
                for dev in devices.data:
                    cols = st.columns([3,2,1])
                    with cols[0]:
                        st.markdown(f"**{dev['device_name']}**")
                    with cols[1]:
                        st.caption(f"Last seen: {dev['last_heartbeat'][:16]}")
                    with cols[2]:
                        if st.button("❌ Remove", key=dev['id'], help="Revoke protection from this device"):
                            supabase.table("active_protection_devices").delete().eq("id", dev['id']).execute()
                            st.success("✅ Device removed — protection stopped")
                            st.rerun()
            else:
                st.info("No active protected devices — install from Chrome Web Store to start.")

        except Exception as e:
            st.error(f"Error loading devices: {str(e)}")

    if user_email == ADMIN_EMAIL:
        with tab5:
            st.title("👤 Registered Companies & Users")
            st.markdown('<div class="compliance-badge">🔐 Admin Access — View and manage all accounts</div>', unsafe_allow_html=True)
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
                    st.subheader("⚙️ Update License Limit")
                    company_options = {f"{row['name']} ({row['email']})": row['id'] for row in all_companies.data}
                    selected_label = st.selectbox("Select company:", list(company_options.keys()))
                    new_limit = st.number_input("New Device Limit", min_value=1, max_value=50000, value=100)
                    
                    if st.button("✅ UPDATE LIMIT"):
                        selected_id = company_options[selected_label]
                        supabase.table("companies").update({"max_devices": new_limit}).eq("id", selected_id).execute()
                        st.success("✅ Limit updated — applies instantly to all devices")
                        st.rerun()

                    st.markdown("---")
                    st.subheader("🗑️ Remove Unwanted Account")
                    selected_label_del = st.selectbox("Select account to remove:", list(company_options.keys()), key="del")
                    
                    if st.button("❌ DELETE ACCOUNT", type="primary", help="This will permanently remove the company and all its data"):
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
                            
                            st.success("✅ Account and all associated data have been removed successfully")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error deleting account: {str(e)}")
                
                else:
                    st.info("No companies have registered yet.")

            except Exception as e:
                st.error(f"❌ Error loading registered users: {str(e)}")

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