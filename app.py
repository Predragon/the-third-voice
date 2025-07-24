import streamlit as st
import requests

st.title("OpenRouter API Test")

# Read API key and model from Streamlit secrets
api_key = st.secrets["openrouter"]["api_key"]
model = st.secrets["MODELS"]["model1"]
api_url = "https://openrouter.ai/api/v1/chat/completions"

# UI input
prompt = st.text_area("Enter your prompt:", "Say hello to the AI!")

if st.button("Send"):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Referer": "https://your-app-url.streamlit.app/"  # update to your actual deployed app if needed
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        st.write("Status code:", response.status_code)
        st.write(response.json())
    except Exception as e:
        st.error(f"Request failed: {e}")
      
