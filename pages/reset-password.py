import streamlit as st
from supabase import create_client

# --- LOAD SAME SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
except Exception as e:
    st.error(f"❌ Secrets Error: {e}")
    st.stop()

auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- PAGE SETUP ---
st.set_page_config(page_title="Reset Password | Shadow AI", page_icon="🔑", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background: #0A0F1F; color: #FFFFFF; font-family: Arial, sans-serif; }
    .login-card { background: rgba(20, 30, 60, 0.85); padding: 40px; border-radius: 8px; border: 2px solid #005EB8; }
    h2 { color: #fff; }
    .stButton>button { background: #005EB8; color: white; font-weight: bold; border-radius: 4px; height: 50px; }
    .stButton>button:hover { background: #003087; }
    </style>
""", unsafe_allow_html=True)

# --- GET TOKEN & EMAIL FROM URL ---
params = st.query_params
token = params.get("token", "")
email = params.get("email", "")

if not token or not email:
    st.error("❌ Invalid or expired link — request a new one")
    st.markdown("<p style='text-align:center;'><a href='/forgot-password' style='color:#4da6ff;'>← Go Back</a></p>", unsafe_allow_html=True)
    st.stop()

# --- PAGE CONTENT ---
st.markdown('<div class="login-card">', unsafe_allow_html=True)
st.subheader("🔑 Set New Password")
new_pass = st.text_input("🔒 New Password", type="password")
confirm_pass = st.text_input("🔒 Confirm Password", type="password")

if st.button("✅ Update Password"):
    if new_pass != confirm_pass:
        st.error("❌ Passwords do not match")
    else:
        try:
            # ✅ Update password using the token
            auth_client.auth.update_user({
                "password": new_pass
            })
            st.success("✅ Password updated successfully!")
            st.markdown("<p style='text-align:center;'><a href='/' style='color:#4da6ff;'>← Go to Login</a></p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
