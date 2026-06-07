import streamlit as st
from supabase import create_client

# --- LOAD SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
except Exception as e:
    st.error(f"❌ Secrets Error: {e}")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- PAGE SETUP ---
st.set_page_config(page_title="Set New Password | Shadow AI", page_icon="🔑", layout="centered")

st.markdown("""
    <style>
    .main { background: #0A0F1F; color: #FFFFFF; font-family: Arial, sans-serif; }
    .card { background: rgba(20, 30, 60, 0.85); padding: 40px; border-radius: 8px; border: 2px solid #005EB8; max-width: 500px; margin: 2rem auto; }
    .stButton>button { background: #005EB8; color: white; width: 100%; height: 50px; font-weight: bold; border-radius: 4px; }
    .stButton>button:hover { background: #003087; }
    a { color: #4da6ff; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- GET EMAIL FROM URL ---
params = st.query_params
email = params.get("email", "")

if not email:
    st.error("❌ Invalid or expired reset link")
    st.markdown("<p style='text-align:center;'><a href='/forgot-password'>← Request New Link</a></p>", unsafe_allow_html=True)
    st.stop()

# --- PAGE CONTENT ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🔑 Create New Password")
st.markdown(f"Resetting password for: **{email}**")

new_pass = st.text_input("🔒 New Password", type="password")
confirm_pass = st.text_input("🔒 Confirm Password", type="password")

if st.button("✅ Update Password"):
    if new_pass != confirm_pass:
        st.error("❌ Passwords do not match")
    elif len(new_pass) < 8:
        st.warning("⚠️ Minimum 8 characters required")
    else:
        try:
            users = supabase.auth.admin.list_users()
            target_user = next((u for u in users if u.email == email), None)
            if not target_user:
                st.error("❌ No account found with this email")
            else:
                supabase.auth.admin.update_user_by_id(target_user.id, {"password": new_pass})
                st.success("✅ Password updated successfully! You can now log in.")
                st.markdown("<p style='text-align:center;'><a href='/'>← Go to Login</a></p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
