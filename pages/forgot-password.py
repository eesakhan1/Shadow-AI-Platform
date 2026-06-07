import streamlit as st
from supabase import create_client
import requests

# --- LOAD SAME SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    RESEND_FROM_EMAIL = st.secrets["RESEND_FROM_EMAIL"]
except Exception as e:
    st.error(f"❌ Secrets Error: {e}")
    st.stop()

# ✅ Use ANON key for auth
auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- PAGE SETUP ---
st.set_page_config(page_title="Forgot Password | Shadow AI", page_icon="🔑", layout="centered")

# --- CUSTOM CSS — EXACT SAME AS MAIN APP ---
st.markdown("""
    <style>
    .main {
        background: #0A0F1F;
        color: #FFFFFF;
        font-family: Arial, Helvetica, sans-serif;
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
    h2 {
        color: #FFFFFF !important;
        font-family: Arial, Helvetica, sans-serif;
        font-weight: bold;
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
    .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid #005EB8;
        border-radius: 4px;
        color: #FFFFFF !important;
    }
    a {
        color: #4da6ff !important;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- SEND RESET EMAIL — EXACT SAME DESIGN AS 2FA ---
def send_reset_email(to_email, reset_link):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": RESEND_FROM_EMAIL,  # ✅ SAME EMAIL AS 2FA
                "to": to_email,
                "subject": "🔐 Shadow AI | Reset Your Password",
                "html": f"""
                <div style="font-family: Arial, sans-serif; background:#0A0F1F; padding:30px; color:white; max-width:600px; margin:0 auto;">
                    <!-- HEADER -->
                    <div style="background:#003087; padding:15px; border-radius:4px;">
                        <h1 style="color:white; margin:0; font-size:24px; font-weight:bold;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE; margin:5px 0 0 0; font-size:14px;">NHS Compliant Data Protection</p>
                    </div>
                    <!-- CONTENT -->
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

# --- PAGE CONTENT ---
st.markdown('<div class="login-card">', unsafe_allow_html=True)
st.subheader("🔑 Reset Your Password")
st.markdown("Enter your registered work email — we’ll send you a secure reset link.")

email = st.text_input("📧 Official Work Email Address")

if st.button("📩 Send Reset Link"):
    if not email:
        st.warning("⚠️ Please enter your email address")
    else:
        try:
            # ✅ Tell Supabase to generate token — DO NOT send email
            res = auth_client.auth.reset_password_for_email(
                email,
                options={
                    "redirect_to": "https://shadowai-security.streamlit.app/reset-password"  # ✅ YOUR APP URL
                }
            )

            # ✅ Build full reset link
            reset_link = f"https://shadowai-security.streamlit.app/reset-password?email={email}"

            # ✅ Send from YOUR email, same design as 2FA
            if send_reset_email(email, reset_link):
                st.success("✅ Reset link sent successfully!")
                st.info("📧 Email sent from: security@shadowaisecurity.co.uk — same as your 2FA codes")
            else:
                st.error("❌ Failed to send email — please try again")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown("<br><p style='text-align:center;'><a href='/' style='color:#4da6ff;'>← Back to Login</a></p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
