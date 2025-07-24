import streamlit as st
import requests

st.title("OpenRouter Multi-Model Test")

# Load API key and models from secrets
api_key = st.secrets["openrouter"]["api_key"]
models = []
try:
    models = [
        st.secrets["MODELS"]["model1"],
        st.secrets["MODELS"]["model2"],
        st.secrets["MODELS"]["model3"],
    ]
except KeyError:
    st.error("Models not properly defined in secrets under [MODELS]. Please check your secrets.toml.")
    st.stop()

api_url = "https://openrouter.ai/api/v1/chat/completions"

prompt = st.text_area("Enter your prompt:", "Say hello to the AI!")

if st.button("Test All Models"):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Referer": "https://your-app-url.streamlit.app/",  # update if needed
    }

    for idx, model in enumerate(models, start=1):
        st.markdown(f"### Model {idx}: `{model}`")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 200,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            st.write("Status code:", response.status_code)

            if response.status_code == 200:
                json_resp = response.json()
                choices = json_resp.get("choices", [])
                if choices:
                    content = choices[0]["message"].get("content", "")
                    st.text_area("Response", content, height=150)
                else:
                    st.warning("No choices in response JSON.")
            else:
                try:
                    st.error(f"Error {response.status_code}: {response.json()}")
                except Exception:
                    st.error(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Request Exception: {e}")

        st.markdown("---")
