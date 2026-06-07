import streamlit as st
import requests

# --- LOAD SECRETS ---
try:
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    RESEND_FROM_EMAIL = st.secrets["RESEND_FROM_EMAIL"]
except Exception as e:
    st.error(f"❌ Secrets Error: {e}")
    st.stop()

# --- PAGE SETUP ---
st.set_page_config(page_title="Forgot Password | Shadow AI", page_icon="🔑", layout="centered")

st.markdown("""
    <style>
    .main { background: #0A0F1F; color: #FFFFFF; font-family: Arial, sans-serif; }
    .card { background: rgba(20, 30, 60, 0.85); padding: 40px; border-radius: 8px; border: 2px solid #005EB8; max-width: 500px; margin: 2rem auto; }
    .stButton>button { background: #005EB8; color: white; width: 100%; height: 50px; font-weight: bold; border-radius: 4px; }
    .stButton>button:hover { background: #003087; }
    a { color: #4da6ff; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- SEND EMAIL ---
def send_reset_email(to_email, link):
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "🔐 Shadow AI | Reset Your Password",
                "html": f"""
                <div style="font-family:Arial,sans-serif; background:#0A0F1F; padding:30px; color:white; max-width:600px; margin:0 auto;">
                    <div style="background:#003087; padding:15px; border-radius:4px;">
                        <h1 style="margin:0; font-size:22px;">🛡️ Shadow AI</h1>
                        <p style="margin:5px 0 0; color:#B0C4DE; font-size:14px;">NHS Compliant Security</p>
                    </div>
                    <div style="padding:20px; background:#141E3C; border-radius:4px; margin-top:15px;">
                        <p>You requested a password reset.</p>
                        <p style="margin:25px 0; text-align:center;">
                            <a href="{link}" style="background:#00A499; color:white; padding:12px 24px; border-radius:4px; text-decoration:none; font-weight:bold;">Reset My Password</a>
                        </p>
                        <p style="font-size:13px; color:#B0C4DE;">Link valid for 60 minutes. Ignore if you didn't request this.</p>
                    </div>
                </div>
                """
            }
        )
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

# --- PAGE CONTENT ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🔑 Reset Your Password")
email = st.text_input("📧 Registered Email Address")

if st.button("📩 Send Reset Link"):
    if not email:
        st.warning("⚠️ Enter your email")
    else:
        # ✅ YOUR EXACT URL — NO MISTAKES NOW
        reset_link = f"https://shadow-ai-platform-4ewudc2yankypfirbaej3.streamlit.app/reset-password?email={email}"
        ok, msg = send_reset_email(email, reset_link)
        if ok:
            st.success("✅ Reset link sent!")
            st.info(f"📧 Sent from: {RESEND_FROM_EMAIL}")
        else:
            st.error(f"❌ Failed: {msg}")

st.markdown("<p style='text-align:center; margin-top:20px;'><a href='/'>← Back to Login</a></p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
