# core/api.py
import requests
import streamlit as st
from config.constants import API_URL

def get_ai_response(message, context, is_received=False):
    if not st.session_state.api_key:
        return {"error": "No API key"}

    prompts = {
        "general": "You are an emotionally intelligent communication coach. Help improve this message for clarity and empathy.",
        "romantic": "You help reframe romantic messages with empathy and clarity while maintaining intimacy.",
        "coparenting": "You offer emotionally safe responses for coparenting focused on the children's wellbeing.",
        "workplace": "You translate workplace messages for professional tone and clear intent.",
        "family": "You understand family dynamics and help rephrase for better family relationships.",
        "friend": "You assist with friendship communication to strengthen bonds and resolve conflicts."
    }

    system_prompt = f"{prompts.get(context, prompts['general'])} {'Analyze this received message and suggest how to respond.' if is_received else 'Improve this message before sending.'}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Message: {message}"}
    ]

    models = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free"
    ]

    for model in models:
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                json={"model": model, "messages": messages},
                timeout=30
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            model_name = model.split("/")[-1].replace(":free", "").replace("-", " ").title()

            return {
                "type": "translate" if is_received else "coach",
                "sentiment": "neutral" if is_received else "improved",
                "meaning": f"Interpretation: {reply[:100]}..." if is_received else None,
                "response": reply if is_received else None,
                "original": message if not is_received else None,
                "improved": reply if not is_received else None,
                "model": model_name
            }
        except Exception:
            continue

    return {"error": "All models failed"}
