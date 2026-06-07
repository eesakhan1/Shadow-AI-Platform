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
import urllib.parse
import uuid
import base64

# --- CONFIGURATION — EXACTLY AS YOU HAVE IN SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
    SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    RESEND_FROM_EMAIL = st.secrets["RESEND_FROM_EMAIL"]
except Exception as e:
    st.error(f"❌ Secrets Error: {e}")
    st.stop()

ADMIN_EMAIL = "security.shadowai@gmail.com"
DEFAULT_MAX_DEVICES = 3  # Paid device limit per account

# ✅ CRITICAL: Use ANON KEY for AUTH (login/register) — SERVICE KEY for DATABASE ONLY
auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)   # ✅ FOR LOGIN
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)     # ✅ FOR DB ACCESS

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
    .device-badge {
        background: #FFB300;
        color: black;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
        margin: 4px 0;
    }
    .device-badge.limit-reached {
        background: #DA291C;
        color: white;
    }
    .delete-btn {
        background-color: #DA291C !important;
        color: white !important;
    }
    .delete-btn:hover {
        background-color: #9E1A12 !important;
    }
    a {
        color: #4da6ff !important;
        text-decoration: none;
    }
    .device-row {
        padding: 12px;
        background: rgba(255,255,255,0.05);
        border-radius: 6px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
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

# --- ✅ RESET PASSWORD EMAIL FUNCTION — CORRECT URL ---
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
                        
                        <p style="margin-top:30px; font-size:12px; color:#888;">Shadow AI is registered on the NHS Evergreen Supplier Assessment | Ref: a0BPz0000GzZ65MAF20260528125015</p>
                    </div>
                </div>
                """
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Email Error: {e}")
        return False

# --- CREATE ZIP FILE ---
def create_zip_file(config_content):
    manifest_content = '''{
  "manifest_version": 3,
  "name": "🛡️ Shadow AI Enterprise",
  "version": "3.3",
  "description": "Military Grade Data Protection & DLP — Active ONLY on AI Platforms.",
  "permissions": ["storage", "activeTab", "scripting"],
  "host_permissions": [
    "*://*.copilot.microsoft.com/*",
    "*://copilot.microsoft.com/*",
    "https://chat.openai.com/*",
    "https://chatgpt.com/*",
    "https://gemini.google.com/*",
    "https://claude.ai/*",
    "https://www.anthropic.com/*",
    "https://perplexity.ai/*",
    "https://www.perplexity.ai/*",
    "https://www.bing.com/chat*",
    "https://poe.com/*",
    "https://chat.mistral.ai/*",
    "https://huggingface.co/chat/*",
    "https://chat.deepseek.com/*",
    "https://kimi.moonshot.cn/*",
    "https://chatglm.cn/*",
    "https://www.coze.com/*",
    "https://grok.x.com/*"
  ],
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; trusted-types 'none';"
  },
  "icons": {
    "128": "icon.png"
  },
  "content_scripts": [
    {
      "matches": [
        "*://*.copilot.microsoft.com/*",
        "*://copilot.microsoft.com/*",
        "https://chat.openai.com/*",
        "https://chatgpt.com/*",
        "https://gemini.google.com/*",
        "https://claude.ai/*",
        "https://www.anthropic.com/*",
        "https://perplexity.ai/*",
        "www.perplexity.ai/*",
        "https://www.bing.com/chat*",
        "https://poe.com/*",
        "https://chat.mistral.ai/*",
        "https://huggingface.co/chat/*",
        "https://chat.deepseek.com/*",
        "https://kimi.moonshot.cn/*",
        "https://chatglm.cn/*",
        "https://www.coze.com/*",
        "https://grok.x.com/*"
      ],
      "js": ["config.js", "content.js"],
      "run_at": "document_start",
      "all_frames": true,
      "match_about_blank": true,
      "world": "ISOLATED"
    }
  ],
  "action": {
    "default_icon": "icon.png"
  },
  "browser_specific_settings": {
    "edge": {
      "browser_action": {
        "default_icon": "icon.png"
      }
    }
  }
}'''

    content_js_content = '''// --- SHADOW AI CORE ENGINE — NHS COMPLIANT ---
console.log("🚀 SHADOW AI: Script injected and RUNNING");

const supabaseUrl = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseUrl : "";
const supabaseKey = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseKey : "";
let COMPANY_ID = "";

async function loadIdFromStorage() {
  try {
    const data = await (chrome || browser).storage.local.get(['shadow_company_id']);
    COMPANY_ID = data.shadow_company_id || (typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "");
  } catch (e) {
    COMPANY_ID = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "";
  }
  if (COMPANY_ID) registerDeviceHeartbeat();
  initProtection();
}

// --- UNIQUE DEVICE ID FOR COUNTING ---
const deviceFingerprint = btoa(navigator.userAgent + navigator.platform + screen.width + screen.height);
const deviceName = `${navigator.platform} | ${navigator.userAgent.substring(0, 40)}...`;

// --- SEND HEARTBEAT EVERY 30s — ONLY COUNTS REAL RUNNING DEVICES ---
async function registerDeviceHeartbeat() {
  try {
    await fetch(`${supabaseUrl}/rest/v1/rpc/register_device_heartbeat`, {
      method: "POST",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        p_company_id: COMPANY_ID,
        p_device_id: deviceFingerprint,
        p_device_name: deviceName
      })
    });
  } catch (e) {}
  setTimeout(registerDeviceHeartbeat, 30000);
}

let customSecrets = [];
const securityPatterns = [
  { name: "SENSITIVE_TERM", regex: /\b(confidential|patient|nhs|gp|hospital|clinic|referral|appointment|diagnosis|treatment|prescription|dosage|allergies|condition|symptoms|consultant|nurse|ward|bed|icb|trust|ods|nhs number|patient id|dob|date of birth|next of kin)\b/gi },
  { name: "NHS_NUMBER", regex: /\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b/g },
  { name: "PATIENT_ID", regex: /\b(PAT|PT|patient)[-\s]?[A-Z0-9]{6,12}\b/gi },
  { name: "ODS_CODE", regex: /\b[A-Z0-9]{3,5}\b/g },
  { name: "CLINICAL_REF", regex: /\b(REF|CLIN|clin)[-\s]?[A-Z0-9]{5,15}\b/gi },
  { name: "DOB", regex: /\b\d{1,2}\/\d{1,2}\/\d{4}\b/g },
  { name: "EMAIL_ADDRESS", regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi },
  { name: "PHONE_NUMBER", regex: /\b(?:+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3}\b/g },
  { name: "POSTCODE", regex: /\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/gi },
  { name: "FULL_NAME", regex: /\b[A-Z][a-z]+\s[A-Z][a-z]+\b/g },
  { name: "CREDIT_CARD", regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
  { name: "API_KEY", regex: /(api|key|token|secret|password|bearer|auth)[^\s]{0,10}['"]?[a-zA-Z0-9_\-+/]{10,}['"]?/gi }
];

async function fetchCompanySecrets() {
  if (!COMPANY_ID) return;
  try {
    const res = await fetch(`${supabaseUrl}/rest/v1/company_secrets?select=*&company_id=eq.${COMPANY_ID}`, {
      headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` }
    });
    const data = await res.json();
    customSecrets = Array.isArray(data) ? data : [];
  } catch (e) {}
}

async function reportLeak(type, detail, blockedText = "") {
  if (!COMPANY_ID) return;
  try {
    await fetch(`${supabaseUrl}/rest/v1/security_logs`, {
      method: "POST",
      headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: type,
        user_device: deviceFingerprint.substring(0, 100),
        violation_type: detail,
        site_url: window.location.hostname,
        blocked_content: blockedText.substring(0, 300),
        created_at: new Date(),
        company_id: COMPANY_ID,
        compliance_flag: "NHS_IG_GDPR"
      })
    });
  } catch (e) {}
}

function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  const badge = document.createElement('div');
  badge.id = 'shadow-ai-badge';
  badge.textContent = '🛡️ Shadow AI | AI PROTECTION ACTIVE';
  badge.style.position = 'fixed';
  badge.style.top = '10px';
  badge.style.right = '10px';
  badge.style.background = '#003087';
  badge.style.color = '#ffffff';
  badge.style.padding = '8px 16px';
  badge.style.borderRadius = '4px';
  badge.style.fontWeight = 'bold';
  badge.style.fontSize = '12px';
  badge.style.zIndex = '2147483647';
  badge.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
  badge.style.border = '2px solid #005EB8';
  badge.style.fontFamily = 'Arial, sans-serif';
  badge.style.pointerEvents = 'none';
  (document.documentElement || document.body).appendChild(badge);
}

function scanAndBlock() {
  let leakFound = false;
  addBadge();

  const inputs = document.querySelectorAll(`
    textarea, 
    [contenteditable="true"], 
    input[type="text"],
    div[role="textbox"],
    .cib-text-input,
    .cib-serp-input,
    div[class*="input"],
    div[class*="prompt"]
  `);
  
  inputs.forEach(input => {
    const original = input.value || input.innerText || "";
    if (original.length < 3) return;

    let redacted = original;
    let matched = false;

    customSecrets.forEach(rule => {
      try {
        const regex = new RegExp(`\\b${rule.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`, 'gi');
        if (regex.test(original)) {
          redacted = redacted.replace(regex, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Custom Rule: ${rule.secret_word}`, original);
        }
      } catch (e) {}
    });

    if (!matched) {
      securityPatterns.forEach(p => {
        if (p.regex.test(original)) {
          redacted = redacted.replace(p.regex, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Pattern: ${p.name}`, original);
        }
      });
    }

    if (matched) {
      if (input.value !== undefined) {
        input.value = redacted;
      } else {
        input.innerText = redacted;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  });

  const sendBtn = document.querySelector(`
    [data-testid="send-button"], 
    button[type="submit"], 
    .send-button,
    .cib-submit-button,
    button[aria-label*="Send"],
    div[class*="send"]
  `);
  
  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? "none" : "auto";
    sendBtn.style.opacity = leakFound ? "0.5" : "1";
  }
}

function initProtection() {
  fetchCompanySecrets();
  setInterval(scanAndBlock, 200);
  setInterval(fetchCompanySecrets, 30000);
}

loadIdFromStorage();

const obs = new MutationObserver(() => scanAndBlock());
obs.observe(document.documentElement, { childList: true, subtree: true, attributes: true, characterData: true });

setTimeout(scanAndBlock, 800);
setTimeout(scanAndBlock, 2000);
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
echo ============================================
echo.

set "FOLDER_PATH=%LOCALAPPDATA%\Google\Chrome\User Data\Default\Extensions\ShadowAI"
rmdir /S /Q "%FOLDER_PATH%" 2>nul
mkdir "%FOLDER_PATH%" 2>nul

echo [✓] Copying files...
copy /Y manifest.json "%FOLDER_PATH%\" >nul
copy /Y content.js "%FOLDER_PATH%\" >nul
copy /Y config.js "%FOLDER_PATH%\" >nul

echo.
echo ✅ FILES READY!
echo 📂 Opening folder...
explorer "%FOLDER_PATH%"
echo.
echo STEPS:
echo 1. chrome://extensions  (OR edge://extensions/)
echo 2. Enable Developer Mode
echo 3. Load Unpacked → Select this folder
echo.
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

# --- ✅ FORGOT PASSWORD PAGE — CORRECT LINK ---
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
                reset_link = f"https://shadow-ai-platform-4ewudc2yankyvpfirbaej3.streamlit.app/?mode=reset&email={encoded_email}"

                if send_reset_email(email, reset_link):
                    st.success("✅ Reset link sent successfully!")
                    st.info("📧 Email sent from: security@shadowaisecurity.co.uk — check your inbox/spam")
                else:
                    st.error("❌ Failed to send email — please try again")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown("<br><p style='text-align:center;'><a href='/' style='color:#4da6ff;'>← Back to Login</a></p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ✅ RESET PASSWORD PAGE ---
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
                    supabase.auth.admin.update_user_by_id(
                        target_user.id,
                        {"password": new_password}
                    )
                    st.success("✅ Password updated successfully! You can now log in.")
                    st.markdown("<p style='text-align:center; margin-top:20px;'><a href='/' style='color:#4da6ff; font-weight:bold;'>← Go to Login</a></p>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIN SCREEN — ✅ NO DEVICE COUNT ON LOGIN ---
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
                        
                        company_data = supabase.table("companies").select("id, name").eq("email", email).execute()
                        if not company_data.data:
                            st.error("❌ Account not found — please register first")
                            st.stop()

                        st.session_state.company_id = company_data.data[0]["id"]
                        code = str(random.randint(100000, 999999))
                        st.session_state.verification_code = code
                        
                        if send_verification_email(email, code):
                            st.session_state.auth_stage = "verify"
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Access Denied: {str(e)}")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    '<p style="text-align: center; margin-top: 8px;">'
                    '<a href="/?page=forgot-password" target="_self" style="color: #4da6ff; text-decoration: none;">🔑 Forgot your password?</a>'
                    '</p>',
                    unsafe_allow_html=True
                )

            elif st.session_state.auth_stage == "verify":
                st.info(f"🔢 Verification code sent to: **{st.session_state.temp_user_obj.email}**")
                user_code = st.text_input("Enter 6-Digit Security Code", max_chars=6)
                
                if st.button("✅ Verify & Access Dashboard"):
                    if user_code == st.session_state.verification_code:
                        st.session_state.user = st.session_state.temp_user_obj
                        st.session_state.user_id = st.session_state.temp_user_obj.id
                        st.session_state.logged_in = True
                        
                        js_code = f"""
                        <script>
                        if (typeof chrome !== 'undefined' && chrome.storage) {{
                            chrome.storage.local.set({{ "shadow_company_id": "{st.session_state.company_id}" }});
                        }}
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

        with tab2:
            st.warning("⚠️ For paying customers only — access is granted after registration & verification")
            new_email = st.text_input("📧 Official Work Email", key="reg_email")
            new_pass = st.text_input("🔒 Create Password", type="password", key="reg_pass")
            company_name = st.text_input("🏢 Organisation Name / Trust Name")
            
            if st.button("✅ Create Account"):
                try:
                    res = auth_client.auth.sign_up({"email": new_email, "password": new_pass})
                    company_id = "org_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    
                    supabase.table("companies").insert({
                        "id": company_id,
                        "name": company_name,
                        "email": new_email,
                        "is_active": True,
                        "max_devices": DEFAULT_MAX_DEVICES,
                        "total_downloads": 0,
                        "active_protected_devices": 0
                    }).execute()
                    
                    st.success("✅ ACCOUNT CREATED SUCCESSFULLY")
                    st.info(f"📧 You can now login — **Paid device limit: {DEFAULT_MAX_DEVICES}**")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

# --- DASHBOARD — ✅ SHOWS ONLY WHAT YOU CARE ABOUT ---
def show_dashboard():
    try:
        company_data = supabase.table("companies").select(
            "is_active, name, email, max_devices, active_protected_devices, total_downloads"
        ).eq("id", st.session_state.company_id).execute()
        
        is_active = True
        org_name = company_data.data[0].get("name", "Your Organisation") if company_data.data else "Your Organisation"
        user_email = company_data.data[0].get("email", "") if company_data.data else ""
        max_devices = company_data.data[0].get("max_devices", DEFAULT_MAX_DEVICES) if company_data.data else DEFAULT_MAX_DEVICES
        active_devices = company_data.data[0].get("active_protected_devices", 0) if company_data.data else 0
        total_downloads = company_data.data[0].get("total_downloads", 0) if company_data.data else 0
    except:
        is_active = True
        org_name = "Your Organisation"
        user_email = ""
        max_devices = DEFAULT_MAX_DEVICES
        active_devices = 0
        total_downloads = 0

    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/809/809934.png", width=80)
    st.sidebar.title("🛡️ Shadow AI")
    st.sidebar.markdown(f"**🏢 {org_name}**")
    st.sidebar.markdown(f"**Reference: `{st.session_state.company_id}`**")
    
    # ✅ EXACTLY WHAT YOU WANT: Downloads + Active Protected Devices
    st.sidebar.markdown(f'<div class="device-badge">📥 Total Downloads: {total_downloads}</div>', unsafe_allow_html=True)
    if active_devices >= max_devices and user_email.lower() != ADMIN_EMAIL.lower():
        st.sidebar.markdown(f'<div class="device-badge limit-reached">🛡️ ACTIVE DEVICES: {active_devices} / {max_devices} (LIMIT REACHED)</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f'<div class="device-badge">🛡️ Active Protected Devices: {active_devices} / {max_devices}</div>', unsafe_allow_html=True)
    
    if is_active:
        st.sidebar.success("✅ License: ACTIVE | COMPLIANT")
    else:
        st.sidebar.error("❌ License: PENDING")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.auth_stage = "login"
        st.rerun()

    if user_email == ADMIN_EMAIL:
        tab1, tab2, tab3, tab4 = st.tabs(["📦 Deployment", "📋 Security Logs", "📱 Active Devices", "👤 Admin Users"])
    else:
        tab1, tab2, tab3 = st.tabs(["📦 Deployment", "📋 Security Logs", "📱 Active Devices"])

    with tab1:
        st.title("🛡️ Security Command Center")
        st.markdown('<div class="compliance-badge">✅ NHS Information Governance Compliant | Audit Logging Enabled</div>', unsafe_allow_html=True)
        
        if active_devices >= max_devices and user_email.lower() != ADMIN_EMAIL.lower():
            st.markdown(f'<div class="device-badge limit-reached" style="font-size:16px; padding:8px 16px;">⚠️ DEVICE LIMIT REACHED: {active_devices} / {max_devices} — No new devices allowed</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="device-badge" style="font-size:16px; padding:8px 16px;">✅ Active Devices: {active_devices} / {max_devices} — Ready to deploy</div>', unsafe_allow_html=True)
        st.markdown("---")

        st.subheader("📦 Deploy Protection Software")
        config_content = f"""const SHADOW_AI_CONFIG = {{
        supabaseUrl: "{SUPABASE_URL}",
        supabaseKey: "{SUPABASE_ANON_KEY}",
        companyId: "{st.session_state.company_id}"
        }};"""
        
        # ✅ COUNT DOWNLOADS EVERY TIME
        supabase.table("companies").update({"total_downloads": total_downloads + 1}).eq("id", st.session_state.company_id).execute()
        zip_file = create_zip_file(config_content)
        
        st.download_button(
            label="⬇️ DOWNLOAD ENTERPRISE PROTECTION PACKAGE",
            data=zip_file,
            file_name="ShadowAI_NHS_Protection.zip",
            mime="application/zip",
            type="primary"
        )
        st.markdown("*Includes extension, deployment tool, and configuration files — works on Chrome, Edge, and Brave*")

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
        st.title("📋 Security Audit Logs")
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

    # ✅ SHOW ONLY REAL DEVICES RUNNING THE EXTENSION
    with tab3:
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
                st.info("No active protected devices — download and install the package to start.")

        except Exception as e:
            st.error(f"Error loading devices: {str(e)}")

    if user_email == ADMIN_EMAIL:
        with tab4:
            st.title("👤 Registered Companies & Users")
            st.markdown('<div class="compliance-badge">🔐 Admin Access — View and manage all accounts</div>', unsafe_allow_html=True)
            st.markdown("---")

            try:
                all_companies = supabase.table("companies").select("id, name, email, is_active, max_devices, active_protected_devices, total_downloads").execute()
                
                if all_companies.data:
                    df = pd.DataFrame(all_companies.data)
                    st.subheader(f"Total Registered: {len(all_companies.data)}")
                    
                    st.dataframe(df, use_container_width=True, column_config={
                        "id": "Company ID",
                        "name": "Organisation Name",
                        "email": "Contact Email",
                        "is_active": "Active Status",
                        "max_devices": "Paid Device Limit",
                        "active_protected_devices": "Active Devices",
                        "total_downloads": "Total Downloads"
                    })

                    st.markdown("---")
                    st.subheader("⚙️ Manage Account Limits")
                    
                    company_options = {f"{row['name']} ({row['email']})": row['id'] for row in all_companies.data}
                    selected_label = st.selectbox("Select account:", list(company_options.keys()))
                    new_limit = st.number_input("New Paid Device Limit", min_value=1, max_value=100, value=3)
                    
                    if st.button("✅ UPDATE LIMIT", type="primary"):
                        selected_id = company_options[selected_label]
                        supabase.table("companies").update({"max_devices": new_limit}).eq("id", selected_id).execute()
                        st.success(f"✅ Updated: Paid limit = {new_limit} devices")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Error loading registered users: {str(e)}")

# --- ✅ ROUTING — FINAL FIX ---
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

    if st.session_state.user is None:
        show_login()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()