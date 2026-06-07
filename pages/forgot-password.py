import streamlit as st
import requests

st.set_page_config(page_title="Forgot Password", layout="centered")

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
st.header("🔑 Reset Your Password")
st.write("Enter your email to receive a secure reset link.")

email = st.text_input("Official Work Email", placeholder="you@nhs.net")

if st.button("Send Reset Link"):
    if not email:
        st.error("Please enter your email address")
    else:
        try:
            res = requests.post(
                "https://ypjpj1xwdjcvlmrmsgc.supabase.co/auth/v1/recover",
                headers={
                    "apikey": st.secrets["SUPABASE_ANON_KEY"],
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "redirect_to": "https://shadow-ai-platform-4ewudc2yankypfirbaej3.streamlit.app/reset-password"
                }
            )
            data = res.json()
            if "error" in data:
                st.error(f"❌ {data['error']['message']}")
            else:
                st.success("✅ Reset link sent! Check your inbox and spam folder.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown("<br><p style='text-align: center;'><a href='/'>← Back to Login</a></p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
