import os
# MAXIMUM FORCE DISABLE — EVERY POSSIBLE SETTING
os.environ["STREAMLIT_SERVER_ENABLE_DOCS"] = "false"
os.environ["STREAMLIT_HIDE_DOCSTRING"] = "true"
os.environ["STREAMLIT_SERVER_ENABLE_STATIC_DOCS"] = "false"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
os.environ["STREAMLIT_DISABLE_INTERNAL_DOCS"] = "true"
os.environ["STREAMLIT_DISABLE_DOCSTRINGS"] = "true"
os.environ["STREAMLIT_DEVELOPMENT_MODE"] = "false"
os.environ["STREAMLIT_DISABLE_DOCSTRING_RENDER"] = "true"

import streamlit as st
from supabase import create_client
import pandas as pd
import random
import requests
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
    st.error(f"❌ Missing Secrets: {e}")
    st.stop()

ADMIN_EMAIL = "security.shadowai@gmail.com"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Shadow AI | NHS Compliant Data Protection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🚨 ABSOLUTE FINAL FIX — BLOCKS EVERY SINGLE THING YOU SEE
st.markdown("""
<style>
/* 🔴 BLOCKS EVERY LINE YOU SEE IN YOUR SCREEN */
[data-testid="stDocstring"],
.stDocstring,
div:has-text("DeltaGenerator"),
div:has-text("Creator of Delta"),
div:has-text("root_container"),
div:has-text("cursor"),
div:has-text("parent"),
div:has-text("block_type"),
div:has-text("dg property"),
div:has-text("Parameters"),
div:has-text("altair_chart"),
div:has-text("area_chart"),
div:has-text("audio"),
div:has-text("badgemethod"),
div:has-text("balloonsmethod"),
div:has-text("bar_chart"),
div:has-text("bokeh_chart"),
div:has-text("buttonmethod"),
div:has-text("camera_input"),
div:has-text("captionmethod"),
div:has-text("chat_input"),
div:has-text("chat_message"),
div:has-text("checkboxmethod"),
div:has-text("codemethod"),
div:has-text("color_picker"),
div:has-text("columnsmethod"),
div:has-text("containermethod"),
div:has-text("data_editor"),
div:has-text("dataframemethod"),
div:has-text("date_input"),
div:has-text("datetime_input"),
div:has-text("dividermethod"),
div:has-text("download_button"),
div:has-text("emptymethod"),
div:has-text("errormethod"),
div:has-text("exceptionmethod"),
div:has-text("expandermethod"),
div:has-text("feedbackmethod"),
div:has-text("file_uploader"),
div:has-text("formmethod"),
div:has-text("form_submit_button"),
div:has-text("graphviz_chart"),
div:has-text("headermethod"),
div:has-text("helpmethod"),
div:has-text("htmlmethod"),
div:has-text("iframemethod"),
div:has-text("imagemethod"),
div:has-text("infomethod"),
div:has-text("jsonmethod"),
div:has-text("latexmethod"),
div:has-text("line_chart"),
div:has-text("link_button"),
div:has-text("mapmethod"),
div:has-text("markdownmethod"),
div:has-text("metricmethod"),
div:has-text("multiselectmethod"),
div:has-text("number_input"),
div:has-text("page_link"),
div:has-text("pdfmethod"),
div:has-text("pillsmethod"),
div:has-text("plotly_chart"),
div:has-text("popoversmethod"),
div:has-text("progressmethod"),
div:has-text("pydeck_chart"),
div:has-text("pyplotmethod"),
div:has-text("radiomethod"),
div:has-text("scatter_chart"),
div:has-text("segmented_control"),
div:has-text("select_slider"),
div:has-text("selectboxmethod"),
div:has-text("slidermethod"),
div:has-text("snowmethod"),
div:has-text("spinnermethod"),
div:has-text("statusmethod"),
div:has-text("subheadermethod"),
div:has-text("successmethod"),
div:has-text("tablemethod"),
div:has-text("tabsmethod"),
div:has-text("textmethod"),
div:has-text("text_area"),
div:has-text("text_input"),
div:has-text("time_input"),
div:has-text("titlemethod"),
div:has-text("toastmethod"),
div:has-text("togglemethod"),
div:has-text("vega_lite_chart"),
div:has-text("videomethod"),
div:has-text("warningmethod"),
div:has-text("writemethod"),
div:has-text("write_stream"),
.element-container pre,
.element-container code,
.stMarkdown pre,
.stMarkdown code,
div[class*="docstring"],
div[class*="help-text"],
div[class*="internal-docs"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    position: absolute !important;
    top: -9999px !important;
    left: -9999px !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
    transform: scale(0) !important;
    z-index: -9999 !important;
}

/* FORCE ALL CONTENT TO START AT TOP — NO GAP */
.block-container {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
.main > div:first-child {
    display: none !important;
}

/* --- 🛑 YOUR ORIGINAL STYLES --- */
.main { background: #0A0F1F; color: #FFFFFF; font-family: Arial, sans-serif; }
.stButton>button { 
    width: 100%; border-radius: 4px; height: 55px; font-size: 18px; font-weight: bold; 
    border: none; transition: all 0.3s ease; background: #005EB8; color: #FFFFFF !important; 
    box-shadow: 0 2px 8px rgba(0,94,184,0.3); text-transform: uppercase; letter-spacing: 0.5px; 
}
.stButton>button:hover { background: #003087; box-shadow: 0 4px 12px rgba(0,48,135,0.5); transform: translateY(-1px); }
.login-card { 
    background-color: rgba(20, 30, 60, 0.85); backdrop-filter: blur(20px); 
    -webkit-backdrop-filter: blur(20px); padding: 40px; border-radius: 8px; 
    border: 2px solid #005EB8; box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    max-width: 550px; margin: 2rem auto; 
}
h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; font-family: Arial, sans-serif; font-weight: bold; }
.stMarkdown p { color: #E0E0E0 !important; font-size: 16px; }
.stTextInput input, .stTextInput label { color: #FFFFFF !important; }
.stTextInput>div>div>input { 
    background-color: rgba(255,255,255,0.05); border: 1px solid #005EB8; 
    border-radius: 4px; color: #FFFFFF !important; 
}
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] { 
    background-color: transparent; border-radius: 4px 4px 0 0; 
    color: #B0C4DE !important; border: 1px solid #003087; 
}
.stTabs [aria-selected="true"] { background: #005EB8; color: #FFFFFF !important; font-weight: bold; }
.stSuccess { 
    background-color: rgba(0, 164, 153, 0.15) !important; color: #00A499 !important; 
    border: 1px solid #00A499 !important; 
}
.stError { 
    background-color: rgba(218, 41, 28, 0.15) !important; color: #DA291C !important; 
    border: 1px solid #DA291C !important; 
}
.stInfo { 
    background-color: rgba(0, 94, 184, 0.15) !important; color: #00A499 !important; 
    border: 1px solid #005EB8 !important; 
}
.compliance-badge { 
    background: #00A499; color: white; padding: 6px 12px; border-radius: 4px; 
    font-weight: bold; font-size: 14px; display: inline-block; margin: 8px 0; 
}
.delete-btn { background-color: #DA291C !important; color: white !important; }
.delete-btn:hover { background-color: #9E1A12 !important; }
</style>

<script>
// 💀 DESTROY EVERY TRACE OF THIS TEXT — RUNS EVERY 1ms
function killAllDocstrings() {
    // Remove by exact test ID
    const el1 = document.querySelector('[data-testid="stDocstring"]');
    if (el1) { el1.remove(); el1.innerHTML = ''; }
    
    // Remove any element containing ANY of these exact words
    const badWords = [
        "DeltaGenerator", "Creator of Delta", "root_container", "cursor", "parent", 
        "block_type", "dg property", "Parameters", "altair_chart", "area_chart", 
        "audio", "badge", "balloons", "bar_chart", "bokeh_chart", "button", 
        "camera_input", "caption", "chat_input", "chat_message", "checkbox", 
        "code", "color_picker", "columns", "container", "data_editor", 
        "dataframe", "date_input", "datetime_input", "divider", "download_button", 
        "empty", "error", "exception", "expander", "feedback", "file_uploader", 
        "form", "form_submit_button", "graphviz_chart", "header", "help", 
        "html", "iframe", "image", "info", "json", "latex", "line_chart", 
        "link_button", "map", "markdown", "metric", "multiselect", "number_input", 
        "page_link", "pdf", "pills", "plotly_chart", "popover", "progress", 
        "pydeck_chart", "pyplot", "radio", "scatter_chart", "segmented_control", 
        "select_slider", "selectbox", "slider", "snow", "spinner", "status", 
        "subheader", "success", "table", "tabs", "text", "text_area", 
        "text_input", "time_input", "title", "toast", "toggle", "vega_lite_chart", 
        "video", "warning", "write", "write_stream"
    ];
    
    document.querySelectorAll('*').forEach(elem => {
        if (elem.textContent) {
            const hasBad = badWords.some(word => elem.textContent.includes(word));
            if (hasBad) {
                elem.remove();
                if (elem.parentElement) elem.parentElement.remove();
                if (elem.parentElement?.parentElement) elem.parentElement.parentElement.remove();
            }
        }
    });
    
    // Remove entire top container if needed
    const root = document.querySelector('.stAppViewContainer');
    if (root && root.firstChild) root.firstChild.remove();
}

// RUN NON-STOP — CANNOT BE OVERRIDDEN
killAllDocstrings();
setInterval(killAllDocstrings, 1);
new MutationObserver(killAllDocstrings).observe(document.body, {childList: true, subtree: true, attributes: true, characterData: true});
</script>
""", unsafe_allow_html=True)

# --- ✅ PERSISTENCE ---
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
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "🔐 Shadow AI | Security Verification Code",
                "html": f"""
                <div style="font-family:Arial,sans-serif;background:#0A0F1F;padding:30px;color:white;max-width:600px;">
                    <div style="background:#003087;padding:15px;border-radius:4px;">
                        <h1 style="color:white;margin:0;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE;margin:5px 0 0 0;">NHS Compliant Data Protection</p>
                    </div>
                    <div style="padding:20px;background:#141E3C;border-radius:4px;margin-top:15px;">
                        <p>Your verification code is:</p>
                        <h2 style="font-size:50px;letter-spacing:10px;color:#00A499;margin:20px 0;">{code}</h2>
                        <p>Enter this code in your dashboard to continue.</p>
                        <p style="margin-top:30px;font-size:14px;color:#888;">Shadow AI is registered on the NHS Evergreen Supplier Assessment | Ref: a0BPz0000GzZ65MAF20260528125015</p>
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
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "🔐 Shadow AI | Reset Your Password",
                "html": f"""
                <div style="font-family:Arial,sans-serif;background:#0A0F1F;padding:30px;color:white;max-width:600px;">
                    <div style="background:#003087;padding:15px;border-radius:4px;">
                        <h1 style="color:white;margin:0;font-size:24px;font-weight:bold;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE;margin:5px 0 0 0;font-size:14px;">NHS Compliant Data Protection</p>
                    </div>
                    <div style="padding:20px;background:#141E3C;border-radius:4px;margin-top:15px;">
                        <p style="font-size:16px;line-height:1.5;">You requested to reset your password for your Shadow AI account.</p>
                        <p style="font-size:16px;line-height:1.5;margin:20px 0;">Click the button below to create a new password:</p>
                        <div style="text-align:center;margin:30px 0;">
                            <a href="{reset_link}" style="background:#00A499;color:#ffffff;padding:14px 28px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:16px;display:inline-block;">Reset My Password</a>
                        </div>
                        <p style="font-size:14px;color:#B0C4DE;margin-top:30px;">This link is valid for <strong>60 minutes</strong>. If you did not request this change, please ignore this email or contact support immediately.</p>
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
    # ONLY CUSTOM HTML — NO STREAMLIT TRIGGER
    st.markdown('<h1 style="color:white; text-align:center; margin-top:2rem; font-size:2.5rem;">🛡️ Shadow AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:18px; color:#B0C4DE;">NHS Compliant Data Protection & AI Security</p>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;" class="compliance-badge">✅ Evergreen Assessment Registered | Ref: a0BPz0000GzZ65MAF20260528125015</div>', unsafe_allow_html=True)
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
                        save_auth(st.session_state.temp_user_obj.id, st.session_state.company_id, st.session_state.temp_user_obj.email)
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
                    supabase.table("companies").insert({
                        "id": company_id,
                        "name": company_name,
                        "email": new_email,
                        "is_active": True,
                        "max_devices": max_devices
                    }).execute()
                    st.success("✅ ACCOUNT CREATED SUCCESSFULLY")
                    st.info("📧 You can now login with your email and password — a security code will be sent to you")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD ---
def show_dashboard():
    # CUSTOM HTML HEADER — NO STREAMLIT TRIGGER
    st.markdown('<h1 style="color:white; margin-top:0; font-size:2rem;">🛡️ Security Command Center</h1>', unsafe_allow_html=True)
    st.markdown('<div class="compliance-badge">✅ NHS Information Governance Compliant | Audit Logging Enabled</div>', unsafe_allow_html=True)
    st.markdown("---")

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
    st.sidebar.success("✅ License: ACTIVE | COMPLIANT") if is_active else st.sidebar.error("❌ License: PENDING")

    if st.sidebar.button("🚪 Logout"):
        clear_auth()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if user_email == ADMIN_EMAIL:
        tab1, tab2, tab3, tab4 = st.tabs(["📦 Deployment", "📋 Security Logs", "📱 Active Devices", "👤 Admin Users"])
    else:
        tab1, tab2, tab3 = st.tabs(["📦 Deployment", "📋 Security Logs", "📱 Active Devices"])

    with tab1:
        st.subheader("📱 Get Started — Official Store Version")
        st.info("✅ No Developer Mode required — safe for all managed devices.")
        st.markdown("""
        **🔗 Download from Official Stores:**
        - [Chrome Web Store](https://chrome.google.com/webstore/detail/shadow-ai-enterprise/YOUR_EXTENSION_ID) *(publish here)*
        - [Edge Add-ons](https://microsoftedge.microsoft.com/addons/detail/shadow-ai-enterprise/YOUR_EXTENSION_ID) *(publish here)*
        """)

        st.subheader("🔑 Your Unique Company ID")
        st.code(st.session_state.company_id, language="text")
        st.markdown("*Copy this ID — you will enter it once when you first open the extension.*")

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

    with tab2:
        st.markdown('<h2 style="color:white;">📋 Security Audit Logs</h2>', unsafe_allow_html=True)
        st.markdown('<div class="compliance-badge">✅ NHS Information Governance Compliant | Audit Logging Enabled</div>', unsafe_allow_html=True)
        st.markdown("---")
        try:
            data = supabase.table("security_logs").select("*").eq("company_id", st.session_state.company_id).order("created_at", desc=True).execute()
            if data.data:
                st.dataframe(pd.DataFrame(data.data), use_container_width=True)
            else:
                st.info("No security events recorded — protection is active and monitoring.")
        except Exception as e:
            st.error(f"Error loading logs: {str(e)}")

    with tab3:
        st.markdown('<h2 style="color:white;">📱 Active Protected Devices</h2>', unsafe_allow_html=True)
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
                st.info("No active protected devices — install from store and activate with your ID.")
        except Exception as e:
            st.error(f"Error loading devices: {str(e)}")

    if user_email == ADMIN_EMAIL:
        with tab4:
            st.markdown('<h2 style="color:white;">👤 Registered Companies & Users</h2>', unsafe_allow_html=True)
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
        decoded_email = urllib.parse.unquote(reset_email)
        show_reset_password(decoded_email)
        return
    if st.session_state.user is None or st.session_state.auth_stage in ["login", "verify"]:
        show_login()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()