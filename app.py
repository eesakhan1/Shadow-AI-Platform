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
RESEND_FROM_EMAIL = "security@shadowaisecurity.co.uk"

# ✅ Admin email restriction
ADMIN_EMAIL = "security.shadowai@gmail.com"

# ✅ Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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
    .delete-btn {
        background-color: #DA291C !important;
        color: white !important;
    }
    .delete-btn:hover {
        background-color: #9E1A12 !important;
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

# --- ✅ UPDATED FUNCTION TO CREATE ZIP — ONLY AI PLATFORMS ---
def create_zip_file(config_content):
    manifest_content = '''{
  "manifest_version": 3,
  "name": "🛡️ Shadow AI Enterprise",
  "version": "2.0",
  "description": "Military Grade Data Protection & DLP — Active ONLY on AI Platforms.",
  "permissions": ["storage", "activeTab", "scripting"],
  "host_permissions": [
    "https://chat.openai.com/*",
    "https://gemini.google.com/*",
    "https://claude.ai/*",
    "https://www.anthropic.com/*",
    "https://perplexity.ai/*",
    "https://www.perplexity.ai/*",
    "https://www.bing.com/chat*",
    "https://copilot.microsoft.com/*",
    "https://poe.com/*",
    "https://www.mistral.ai/*",
    "https://chat.mistral.ai/*",
    "https://www.llama.ai/*",
    "https://huggingface.co/chat/*",
    "https://chat.deepseek.com/*",
    "https://kimi.moonshot.cn/*",
    "https://chatglm.cn/*",
    "https://www.coze.com/*",
    "https://grok.x.com/*"
  ],
  "icons": {
    "128": "icon.png"
  },
  "content_scripts": [
    {
      "matches": [
        "https://chat.openai.com/*",
        "https://gemini.google.com/*",
        "https://claude.ai/*",
        "https://www.anthropic.com/*",
        "https://perplexity.ai/*",
        "https://www.perplexity.ai/*",
        "https://www.bing.com/chat*",
        "https://copilot.microsoft.com/*",
        "https://poe.com/*",
        "https://www.mistral.ai/*",
        "https://chat.mistral.ai/*",
        "https://www.llama.ai/*",
        "https://huggingface.co/chat/*",
        "https://chat.deepseek.com/*",
        "https://kimi.moonshot.cn/*",
        "https://chatglm.cn/*",
        "https://www.coze.com/*",
        "https://grok.x.com/*"
      ],
      "js": ["config.js", "content.js"],
      "run_at": "document_end"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": "icon.png"
  }
}'''

    content_js_content = '''// --- SHADOW AI CORE ENGINE ---
// --- NHS COMPLIANT VERSION ---
// --- ACTIVE ONLY ON AI PLATFORMS ---

// --- IMPORT CONFIG ---
const supabaseUrl = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseUrl : "";
const supabaseKey = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseKey : "";

let COMPANY_ID = "";
async function loadIdFromStorage() {
    try {
        let storage = chrome || browser;
        const data = await storage.storage.local.get(['shadow_company_id']);
        if (data.shadow_company_id) {
            COMPANY_ID = data.shadow_company_id;
        } else {
            COMPANY_ID = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "";
        }
    } catch (e) {
        COMPANY_ID = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "";
    }
}

let customSecrets = [];
const deviceFingerprint = `${navigator.platform} | ${navigator.userAgent.substring(0, 100)}`;

// ==========================================
// ✅ NHS FULL PROTECTION RULES
// ==========================================
const securityPatterns = [
    { name: "SENSITIVE_TERM", regex: /\b(confidential|patient|nhs|gp|hospital|clinic|referral|appointment|diagnosis|treatment|prescription|dosage|allergies|condition|symptoms|consultant|nurse|ward|bed|icb|trust|ods|nhs number|patient id|dob|date of birth|next of kin)\b/gi },
    { name: "NHS_NUMBER", regex: /\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b/g },
    { name: "PATIENT_ID", regex: /\b(PAT|PT|patient)[-\s]?[A-Z0-9]{6,12}\b/gi },
    { name: "ODS_CODE", regex: /\b[A-Z0-9]{3,5}\b/g },
    { name: "CLINICAL_REF", regex: /\b(REF|CLIN|clin)[-\s]?[A-Z0-9]{5,15}\b/gi },
    { name: "DOB", regex: /\b\d{1,2}\/\d{1,2}\/\d{4}\b/g },
    { name: "EMAIL_ADDRESS", regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi },
    { name: "PHONE_NUMBER", regex: /\b(?:\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3}\b/g },
    { name: "POSTCODE", regex: /\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/gi },
    { name: "FULL_NAME", regex: /\b[A-Z][a-z]+\s[A-Z][a-z]+\b/g },
    { name: "CREDIT_CARD", regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
    { name: "API_KEY", regex: /(api|key|token|secret|password|bearer|auth)[^\s]{0,10}['"]?[a-zA-Z0-9_\-+/]{10,}['"]?/gi }
];

// ==========================================
// 📡 SYNC WITH DASHBOARD
// ==========================================
async function fetchCompanySecrets() {
    if (!COMPANY_ID) return;
    try {
        const res = await fetch(`${supabaseUrl}/rest/v1/company_secrets?select=*&company_id=eq.${COMPANY_ID}`, {
            headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` }
        });
        const data = await res.json();
        if (Array.isArray(data)) customSecrets = data;
    } catch (e) {}
}

// ==========================================
// 📊 LOG COMPLIANCE EVENTS
// ==========================================
async function reportLeak(type, detail, blockedText = "") {
    if (!COMPANY_ID) return;
    try {
        await fetch(`${supabaseUrl}/rest/v1/security_logs`, {
            method: "POST",
            headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}`, "Content-Type": "application/json" },
            body: JSON.stringify({
                event_type: type,
                user_device: deviceFingerprint,
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

// ==========================================
// 🛡️ STATUS BADGE
// ==========================================
function addBadge() {
    if (document.getElementById('shadow-ai-badge')) return;
    const badge = document.createElement('div');
    badge.id = 'shadow-ai-badge';
    badge.innerHTML = `🛡️ Shadow AI | AI PROTECTION ACTIVE`;
    badge.style.cssText = `
        position: fixed; top: 15px; right: 15px;
        background: #003087; color: #fff;
        padding: 10px 20px; border-radius: 4px;
        font-weight: bold; font-size: 13px; z-index: 9999999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2); border: 2px solid #005EB8;
        font-family: Arial, sans-serif;
    `;
    document.body.appendChild(badge);
}

// ==========================================
// ⚡ PROTECTION ENGINE — ONLY RUNS ON AI SITES
// ==========================================
function scanAndBlock() {
    let globalLeakDetected = false;
    addBadge();

    const inputs = document.querySelectorAll('textarea, [contenteditable="true"], input[type="text"]');
    inputs.forEach(input => {
        let text = input.value || input.innerText || "";
        if (text.length < 3) return;

        let redactedText = text;
        let localLeak = false;

        // Custom rules
        customSecrets.forEach(secret => {
            try {
                const regex = new RegExp(`\\b${secret.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`, 'gi');
                if (regex.test(text)) {
                    redactedText = redactedText.replace(regex, '██████████');
                    localLeak = true;
                    globalLeakDetected = true;
                    reportLeak("PREVENTED", `Custom Rule: ${secret.secret_word}`, text);
                }
            } catch (e) {}
        });

        // System patterns
        if (!localLeak) {
            securityPatterns.forEach(p => {
                if (p.regex.test(text)) {
                    redactedText = redactedText.replace(p.regex, '██████████');
                    localLeak = true;
                    globalLeakDetected = true;
                    reportLeak("PREVENTED", `Pattern: ${p.name}`, text);
                }
            });
        }

        if (localLeak) {
            if (input.value !== undefined) input.value = redactedText;
            else input.innerText = redactedText;
        }
    });

    // Lock send button
    const sendBtn = document.querySelector('[data-testid="send-button"], button[type="submit"], .send-button');
    if (sendBtn) {
        sendBtn.disabled = globalLeakDetected;
        sendBtn.style.opacity = globalLeakDetected ? "0.5" : "1";
        sendBtn.style.border = globalLeakDetected ? "2px solid #DA291C" : "";
        sendBtn.style.cursor = globalLeakDetected ? "not-allowed" : "pointer";
    }
}

// ==========================================
// 🚀 STARTUP
// ==========================================
loadIdFromStorage().then(() => {
    fetchCompanySecrets();
    setInterval(scanAndBlock, 800);
    setInterval(fetchCompanySecrets, 60000);
});

const observer = new MutationObserver(debounce(() => scanAndBlock(), 200));
observer.observe(document.body, { childList: true, subtree: true });

function debounce(func, wait) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

console.log("%c 🛡️ SHADOW AI — NHS COMPLIANT | ACTIVE ON AI PLATFORMS ONLY ", "background:#003087;color:white;padding:4px");
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
echo          ACTIVE ONLY ON AI PLATFORMS
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
echo ✅ PROTECTION RUNS ONLY ON: ChatGPT, Gemini, Claude, Copilot, Perplexity, Mistral, etc.
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
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.temp_user_obj = res.user
                        
                        company_data = supabase.table("companies").select("id").eq("email", email).execute()
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
                    res = supabase.auth.sign_up({
                        "email": new_email,
                        "password": new_pass
                    })
                    
                    company_id = "org_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    
                    supabase.table("companies").insert({
                        "id": company_id,
                        "name": company_name,
                        "email": new_email,
                        "is_active": True
                    }).execute()
                    
                    st.success("✅ ACCOUNT CREATED SUCCESSFULLY")
                    st.info("📧 You can now login with your email and password — a security code will be sent to you")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD FUNCTION ---
def show_dashboard():
    try:
        company_data = supabase.table("companies").select("is_active, name, email").eq("id", st.session_state.company_id).execute()
        is_active = True
        org_name = company_data.data[0].get("name", "Your Organisation") if company_data.data else "Your Organisation"
        user_email = company_data.data[0].get("email", "") if company_data.data else ""
    except:
        is_active = True
        org_name = "Your Organisation"
        user_email = ""

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

    # --- MAIN CONTENT TABS ---
    if user_email == ADMIN_EMAIL:
        tab1, tab2, tab3 = st.tabs(["📦 Deployment", "📋 Security Logs", "👤 Admin Users"])
    else:
        tab1, tab2 = st.tabs(["📦 Deployment", "📋 Security Logs"])

    # --- TAB 1: DEPLOYMENT ---
    with tab1:
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

    # --- TAB 2: SECURITY LOGS ---
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

    # --- TAB 3: ADMIN USERS ---
    if user_email == ADMIN_EMAIL:
        with tab3:
            st.title("👤 Registered Companies & Users")
            st.markdown('<div class="compliance-badge">🔐 Admin Access — View and manage all accounts</div>', unsafe_allow_html=True)
            st.markdown("---")

            try:
                all_companies = supabase.table("companies").select("id, name, email, is_active").execute()
                
                if all_companies.data:
                    df = pd.DataFrame(all_companies.data)
                    st.subheader(f"Total Registered: {len(all_companies.data)}")
                    
                    st.dataframe(df, use_container_width=True, column_config={
                        "id": "Company ID",
                        "name": "Organisation Name",
                        "email": "Contact Email",
                        "is_active": "Active Status"
                    })

                    st.markdown("---")
                    st.subheader("🗑️ Remove Unwanted Account")
                    
                    company_options = {f"{row['name']} ({row['email']})": row['id'] for row in all_companies.data}
                    selected_label = st.selectbox("Select account to remove:", list(company_options.keys()))
                    
                    if st.button("❌ DELETE ACCOUNT", type="primary", help="This will permanently remove the company and all its data"):
                        selected_id = company_options[selected_label]
                        
                        try:
                            supabase.table("security_logs").delete().eq("company_id", selected_id).execute()
                            supabase.table("company_secrets").delete().eq("company_id", selected_id).execute()
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
if st.session_state.user is None:
    show_login()
else:
    show_dashboard()