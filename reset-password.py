import streamlit as st
import requests

st.set_page_config(page_title="Set New Password", layout="centered")

st.markdown("""
<style>
.container { max-width: 450px; margin: 3rem auto; padding: 2rem; border-radius: 8px; border: 2px solid #005EB8; background: #141E3C; }
h2 { color: #fff; text-align: center; }
input { width: 100%; padding: 10px; margin: 8px 0; border-radius: 4px; border: 1px solid #005EB8; background: rgba(255,255,255,0.05); color: white; }
button { width: 100%; padding: 10px; background: #005EB8; color: white; border: none; border-radius: 4px; font-weight: bold; }
a { color: #4da6ff; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="container">', unsafe_allow_html=True)
st.header("🔒 Create New Password")

# Get token from URL
params = st.query_params
access_token = params.get("access_token")

if not access_token:
    st.warning("⚠️ Invalid or expired link. Please request a new one.")
    st.markdown("<p style='text-align: center;'><a href='/forgot-password'>→ Request New Link</a></p>", unsafe_allow_html=True)
else:
    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm Password", type="password")

    if st.button("Update Password"):
        if new_pass != confirm_pass:
            st.error("❌ Passwords do not match")
        elif len(new_pass) < 6:
            st.error("❌ Password must be at least 6 characters")
        else:
            try:
                res = requests.put(
                    "https://ypjpj1xwdjcvlmrmsgc.supabase.co/auth/v1/user",
                    headers={
                        "apikey": st.secrets["SUPABASE_ANON_KEY"],
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={"password": new_pass}
                )
                data = res.json()
                if "error" in data:
                    st.error(f"❌ {data['error']['message']}")
                else:
                    st.success("✅ Password updated successfully!")
                    st.markdown("<p style='text-align: center;'><a href='/'>→ Go to Login</a></p>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)