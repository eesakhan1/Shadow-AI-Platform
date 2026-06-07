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
st.set_page_config(page_title="Set New Password | Shadow AI", page_icon="🔑", layout="centered")

# --- SAME CSS ---
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

# --- GET EMAIL FROM URL ---
params = st.query_params
email = params.get("email", "")

if not email:
    st.error("❌ Invalid or expired link — please request a new one")
    st.markdown("<p style='text-align:center;'><a href='/forgot-password' style='color:#4da6ff;'>← Request New Link</a></p>", unsafe_allow_html=True)
    st.stop()

# --- PAGE CONTENT ---
st.markdown('<div class="login-card">', unsafe_allow_html=True)
st.subheader("🔑 Create New Password")
st.markdown(f"Setting new password for: **{email}**")

new_password = st.text_input("🔒 New Password", type="password")
confirm_password = st.text_input("🔒 Confirm New Password", type="password")

if st.button("✅ Update Password"):
    if new_password != confirm_password:
        st.error("❌ Passwords do not match — please retype")
    elif len(new_password) < 6:
        st.warning("⚠️ Password must be at least 6 characters")
    else:
        try:
            # ✅ Update password directly
            auth_client.auth.admin.update_user_by_id(
                email,
                {"password": new_password}
            )
            st.success("✅ Password updated successfully!")
            st.markdown("<p style='text-align:center; margin-top:20px;'><a href='/' style='color:#4da6ff; font-weight:bold;'>← Go to Login</a></p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
