import streamlit as st
from supabase import create_client
import requests
import urllib.parse

# --- Load secrets ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
    SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    RESEND_FROM_EMAIL = st.secrets["RESEND_FROM_EMAIL"]
except Exception as e:
    st.error(f"❌ Secrets missing: {e}")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- Page config ---
st.set_page_config(page_title="Password Reset | Shadow AI", page_icon="🔑", layout="centered")

st.markdown("""
    <style>
    .main { background: #0A0F1F; color: #FFFFFF; font-family: Arial, sans-serif; }
    .card { background: rgba(20, 30, 60, 0.85); padding: 40px; border-radius: 8px; border: 2px solid #005EB8; max-width: 500px; margin: 2rem auto; }
    .stButton>button { background: #005EB8; color: white; width: 100%; height: 50px; font-weight: bold; border-radius: 4px; }
    .stButton>button:hover { background: #003087; }
    a { color: #4da6ff; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- Send reset email ---
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
                        <p>You requested a password reset for your Shadow AI account.</p>
                        <p style="margin:25px 0; text-align:center;">
                            <a href="{link}" style="background:#00A499; color:white; padding:12px 24px; border-radius:4px; text-decoration:none; font-weight:bold;">Reset My Password</a>
                        </p>
                        <p style="font-size:13px; color:#B0C4DE;">This link is valid for 60 minutes. If you did not request this, please ignore this email.</p>
                    </div>
                </div>
                """
            }
        )
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

# --- Check if we are in reset mode ---
params = st.query_params
reset_email = params.get("reset_email", "")

# --- If reset link is opened, show password form ---
if reset_email:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔑 Create New Password")
    st.markdown(f"Resetting password for: **{reset_email}**")

    new_pass = st.text_input("🔒 New Password", type="password")
    confirm_pass = st.text_input("🔒 Confirm Password", type="password")

    if st.button("✅ Update Password"):
        if new_pass != confirm_pass:
            st.error("❌ Passwords do not match")
        elif len(new_pass) < 8:
            st.warning("⚠️ Minimum 8 characters required")
        else:
            try:
                users = supabase_admin.auth.admin.list_users()
                target_user = next((u for u in users if u.email == reset_email), None)
                if not target_user:
                    st.error("❌ No account found with this email")
                else:
                    supabase_admin.auth.admin.update_user_by_id(target_user.id, {"password": new_pass})
                    st.success("✅ Password updated successfully! You can now log in.")
                    st.markdown("<p style='text-align:center;'><a href='/'>← Go to Login</a></p>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- Default: Show forgot password form ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🔑 Reset Your Password")
email = st.text_input("📧 Registered Email Address")

if st.button("📩 Send Reset Link"):
    if not email:
        st.warning("⚠️ Please enter your email address")
    else:
        # ✅ Link points to THIS SAME PAGE — no more missing pages!
        encoded_email = urllib.parse.quote(email)
        reset_link = f"https://shadow-ai-platform-4ewudc2yankypfirbaej3.streamlit.app/forgot-password?reset_email={encoded_email}"
        
        ok, msg = send_reset_email(email, reset_link)
        if ok:
            st.success("✅ Reset link sent successfully!")
            st.info(f"📧 Sent from: {RESEND_FROM_EMAIL} — check your inbox or spam folder")
        else:
            st.error(f"❌ Failed to send: {msg}")

st.markdown("<p style='text-align:center; margin-top:20px;'><a href='/'>← Back to Login</a></p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
