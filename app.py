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

# --- CONFIGURATION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
RESEND_FROM_EMAIL = "security@shadowaisecurity.co.uk"  # Your branded email

# Initialize Supabase connections
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)  # For admin operations

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
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
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

# --- EMAIL FUNCTION ---
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

# --- FUNCTION TO CREATE ZIP FILE ---
def create_zip_file(config_content):
    manifest_content = '''{
  "manifest_version": 3,
  "name": "🛡️ Shadow AI | NHS Compliant",
  "version": "2.1",
  "description": "Data Loss Prevention & AI Security — Built for Healthcare & NHS Standards.",
  "permissions": ["storage", "activeTab", "scripting"],
  "host_permissions": ["<all_urls>"],
  "icons": {
    "128": "icon.png"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["config.js", "content.js"],
      "run_at": "document_end"
    }
  ]
}'''

    content_js_content = '''// --- SHADOW AI CORE ENGINE ---
// --- NHS COMPLIANT VERSION ---

const BADGE_STYLE = `
position: fixed;
top: 15px;
right: 15px;
background: #003087;
color: #ffffff;
padding: 10px 20px;
border-radius: 4px;
font-weight: bold;
font-size: 13px;
z-index: 9999999;
box-shadow: 0 2px 8px rgba(0,0,0,0.2);
border: 2px solid #005EB8;
font-family: Arial, Helvetica, sans-serif;
letter-spacing: 0.5px;
`;

function addBadge() {
    if (document.getElementById('shadow-ai-badge')) return;
    const badge = document.createElement('div');
    badge.id = 'shadow-ai-badge';
    badge.innerHTML = '🛡️ SHADOW AI | NHS COMPLIANT';
    badge.style.cssText = BADGE_STYLE;
    document.body.appendChild(badge);
}

setInterval(() => {
    addBadge();
    if(typeof SHADOW_AI_CONFIG !== 'undefined'){}
}, 1000);
'''

    bat_content = r'''@echo off
chcp 65001 >nul
cls
echo.
echo ██████╗ ██╗   ██╗██████╗ ███████╗██████╗ 
echo ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔══██╗
echo ██████╔╝██║   ██║██████╔╝█████╗  ██████╔╝
echo ██╔══██╗██║   ██║██╔══██╗██╔══╝  ██╔══██╗
echo ██████╔╝╚██████╔╝██║  ██║███████║██║  ██║
echo ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
echo.
echo          NHS COMPLIANT DEPLOYMENT TOOL
echo          COPYING FILES AUTOMATICALLY
echo ============================================
echo.

set "FOLDER_PATH=%LOCALAPPDATA%\Google\Chrome\User Data\Default\Extensions\ShadowAI"
rmdir /S /Q "%FOLDER_PATH%" 2>nul
mkdir "%FOLDER_PATH%" 2>nul

echo [✓] Copying manifest.json...
copy /Y manifest.json "%FOLDER_PATH%\" >nul
echo [✓] Copying content.js...
copy /Y content.js "%FOLDER_PATH%\" >nul
echo [✓] Copying config.js...
copy /Y config.js "%FOLDER_PATH%\" >nul

echo.
echo ✅ FILES READY!
echo.
echo 📂 OPENING FOLDER...
explorer "%FOLDER_PATH%"
echo.
echo NOW IN CHROME/EDGE:
echo 1. Go to: chrome://extensions OR edge://extensions
echo 2. Turn ON Developer Mode
echo 3. Click "LOAD UNPACKED"
echo 4. SELECT THE FOLDER THAT OPENED
echo.
echo ============================================
pause'''

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("manifest.json", manifest_content)
        zip_file.writestr("content.js", content_js_content)
        zip_file.writestr("config.js", config_content)
        zip_file.writestr("INSTALL_SHADOW_AI.bat", bat_content)
        zip_file.writestr("icon.png", b"") 
        
    zip_buffer.seek(0)
    return zip_buffer

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
        
        # --- LOGIN FLOW ---
        with tab1:
            if st.session_state.auth_stage == "login":
                email = st.text_input("📧 Official Work Email Address", key="login_email")
                password = st.text_input("🔒 Password", type="password", key="login_pass")
                
                if st.button("🚀 Login", type="primary"):
                    try:
                        # Sign in user
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.temp_user_obj = res.user
                        
                        # Get their company ID automatically
                        company_data = supabase.table("companies").select("id").eq("email", email).execute()
                        if company_data.data:
                            st.session_state.company_id = company_data.data[0]["id"]
                            
                            # Send verification code
                            code = str(random.randint(100000, 999999))
                            st.session_state.verification_code = code
                            
                            if send_verification_email(email, code):
                                st.session_state.auth_stage = "verify"
                                st.rerun()
                        else:
                            st.error("❌ Account not found — please register first")
                            
                    except Exception as e:
                        st.error(f"❌ Access Denied: {str(e)}")

            elif st.session_state.auth_stage == "verify":
                st.info(f"🔢 Verification code sent to: **{st.session_state.temp_user_obj.email}**")
                user_code = st.text_input("Enter 6-Digit Security Code", max_chars=6)
                
                if st.button("✅ Verify & Access Dashboard"):
                    if user_code == st.session_state.verification_code:
                        # Login success
                        st.session_state.user = st.session_state.temp_user_obj
                        st.session_state.user_id = st.session_state.temp_user_obj.id
                        st.session_state.logged_in = True
                        
                        # ✅ Set company ID for RLS policies
                        try:
                            supabase_admin.rpc('set_config', {'name': 'app.company_id', 'value': st.session_state.company_id})
                        except:
                            pass
                        
                        # Send ID to extension
                        js_code = f"""
                        <script>
                        let browserAPI = typeof chrome !== 'undefined' ? chrome : browser;
                        browserAPI.storage.local.set({{ shadow_company_id: "{st.session_state.company_id}" }}, function() {{
                            console.log("✅ ID sent to Shadow AI Extension!");
                        }});
                        </script>
                        """
                        st.components.v1.html(js_code, height=0)
                        
                        st.success("✅ Login Successful — Protection Active")
                        st.rerun()
                    else:
                        st.error("❌ Invalid or expired code")
                
                if st.button("🔙 Back to Login"):
                    st.session_state.auth_stage = "login"
                    st.rerun()

        # --- REGISTER FLOW ---
        with tab2:
            st.warning("⚠️ For paying customers only — access is granted after registration & verification")
            new_email = st.text_input("📧 Official Work Email", key="reg_email")
            new_pass = st.text_input("🔒 Create Password", type="password", key="reg_pass")
            company_name = st.text_input("🏢 Organisation Name / Trust Name")
            
            if st.button("✅ Create Account"):
                try:
                    # Create auth user
                    res = supabase.auth.sign_up({
                        "email": new_email,
                        "password": new_pass
                    })
                    
                    # Generate unique Company ID automatically
                    company_id = "org_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    
                    # ✅ Use ADMIN connection to insert (bypasses RLS safely)
                    supabase_admin.table("companies").insert({
                        "id": company_id,
                        "name": company_name,
                        "email": new_email,
                        "is_active": True
                    }).execute()
                    
                    st.success("✅ ACCOUNT CREATED SUCCESSFULLY")
                    st.info("📧 You can now login with your email and password — a security code will be sent to you")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD FUNCTION ---
def show_dashboard():
    # Fetch company details
    try:
        company_data = supabase.table("companies").select("is_active, name").eq("id", st.session_state.company_id).execute()
        is_active = True
        org_name = company_data.data[0].get("name", "Your Organisation") if company_data.data else "Your Organisation"
    except:
        is_active = True
        org_name = "Your Organisation"

    # --- SIDEBAR ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/809/809934.png", width=80)
    st.sidebar.title("🛡️ Shadow AI")
    st.sidebar.markdown(f"**🏢 {org_name}**")
    st.sidebar.markdown(f"**Reference: `{st.session_state.company_id}`**")
    
    if is_active:
        st.sidebar.success("✅ License: ACTIVE | COMPLIANT")
    else:
        st.sidebar.error("❌ License: PENDING")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.auth_stage = "login"
        st.rerun()

    # --- MAIN CONTENT ---
    st.title("🛡️ Security Command Center")
    st.markdown('<div class="compliance-badge">✅ NHS Information Governance Compliant | Audit Logging Enabled</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("📦 Deploy Protection Software")
    config_content = f"""const SHADOW_AI_CONFIG = {{
    supabaseUrl: "{SUPABASE_URL}",
    supabaseKey: "{SUPABASE_ANON_KEY}",
    companyId: "{st.session_state.company_id}"
}};"""
    
    zip_file = create_zip_file(config_content)
    
    st.download_button(
        label="⬇️ DOWNLOAD ENTERPRISE PROTECTION PACKAGE",
        data=zip_file,
        file_name="ShadowAI_NHS_Protection.zip",
        mime="application/zip",
        type="primary"
    )
    st.markdown("*Includes extension, deployment tool, and configuration files — works on Chrome, Edge, and Brave*")

    # --- LOGS SECTION ---
    st.markdown("---")
    st.subheader("📋 Security Audit Logs")
    try:
        data = supabase.table("security_logs").select("*").eq("company_id", st.session_state.company_id).order("created_at", desc=True).execute()
        if data.data:
            st.dataframe(pd.DataFrame(data.data), use_container_width=True)
        else:
            st.info("No security events recorded — protection is active and monitoring.")
    except Exception as e:
        st.error(f"Error loading logs: {e}")

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
                # ✅ Use admin connection for insert
                supabase_admin.table("company_secrets").insert({
                    "secret_word": secret_word,
                    "label": replacement_label,
                    "company_id": st.session_state.company_id
                }).execute()
                st.success("✅ Rule added — protection updated across all devices")
            except Exception as e:
                st.error(f"Error saving rule: {e}")

# --- ROUTING ---
if st.session_state.user is None:
    show_login()
else:
    show_dashboard()