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

# --- CUSTOM CSS (same style) ---
st.markdown("""
    <style>
    .main { background: #0A0F1F; color: #FFFFFF; font-family: Arial, sans-serif; }
    .login-card { background: rgba(20, 30, 60, 0.85); padding: 40px; border-radius: 8px; border: 2px solid #005EB8; }
    h2 { color: #fff; }
    .stButton>button { background: #005EB8; color: white; font-weight: bold; border-radius: 4px; height: 50px; }
    .stButton>button:hover { background: #003087; }
    </style>
""", unsafe_allow_html=True)

# --- SEND RESET EMAIL via RESEND ---
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
                <div style="font-family: Arial, sans-serif; background:#0A0F1F; padding:30px; color:white; max-width:600px;">
                    <div style="background:#003087; padding:15px; border-radius:4px;">
                        <h1 style="color:white; margin:0;">🛡️ Shadow AI</h1>
                        <p style="color:#B0C4DE; margin:5px 0 0 0;">NHS Compliant Data Protection</p>
                    </div>
                    <div style="padding:20px; background:#141E3C; border-radius:4px; margin-top:15px;">
                        <p>You requested to reset your password. Click the link below:</p>
                        <p style="margin:20px 0;">
                            <a href="{reset_link}" style="background:#00A499; color:white; padding:12px 24px; border-radius:4px; text-decoration:none; font-weight:bold;">
                                Reset Password
                            </a>
                        </p>
                        <p style="font-size:14px; color:#888;">Link valid for 1 hour. If you didn't request this, ignore this email.</p>
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
st.subheader("🔑 Forgot Password")
email = st.text_input("📧 Enter your work email")

if st.button("📩 Send Reset Link"):
    try:
        # ✅ Tell Supabase to create the reset token (but NOT send email)
        res = auth_client.auth.reset_password_for_email(
            email,
            options={
                "redirect_to": "https://shadowai-security.streamlit.app/reset-password"  # ✅ YOUR APP URL
            }
        )

        # ✅ Build the full reset link (we send it ourselves)
        reset_link = f"https://shadowai-security.streamlit.app/reset-password?token={res.data.get('token', '')}&email={email}"

        # ✅ SEND FROM YOUR EMAIL via RESEND
        if send_reset_email(email, reset_link):
            st.success("✅ Reset link sent! Check your inbox (from security@shadowaisecurity.co.uk)")
            st.info("📧 Same sender as your 2FA codes — perfect!")
        else:
            st.error("❌ Failed to send email")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

st.markdown("<br><p style='text-align:center;'><a href='/' style='color:#4da6ff;'>← Back to Login</a></p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
