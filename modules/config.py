"""
Configuration and constants for The Third Voice AI
Created with love for Samantha and all families 💖
"""

import streamlit as st

# API Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUIRE_TOKEN = False

# Valid beta tokens for access control
VALID_TOKENS = ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]

# Relationship contexts for personalized coaching
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]

# AI Models (fallback chain for reliability)
AI_MODELS = [
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free", 
    "microsoft/phi-3-mini-128k-instruct:free"
]

# CSS Styles for beautiful UI
CSS_STYLES = """
<style>
.contact-card {
    background: rgba(76,175,80,0.1);
    padding: 0.8rem;
    border-radius: 8px;
    border-left: 4px solid #4CAF50;
    margin: 0.5rem 0;
    cursor: pointer;
}

.ai-response {
    background: rgba(76,175,80,0.1);
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #4CAF50;
    margin: 0.5rem 0;
}

.user-msg {
    background: rgba(33,150,243,0.1);
    padding: 0.8rem;
    border-radius: 8px;
    border-left: 4px solid #2196F3;
    margin: 0.3rem 0;
}

.contact-msg {
    background: rgba(255,193,7,0.1);
    padding: 0.8rem;
    border-radius: 8px;
    border-left: 4px solid #FFC107;
    margin: 0.3rem 0;
}

.pos {
    background: rgba(76,175,80,0.2);
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.2rem 0;
}

.neg {
    background: rgba(244,67,54,0.2);
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.2rem 0;
}

.neu {
    background: rgba(33,150,243,0.2);
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.2rem 0;
}

.journal-section {
    background: rgba(156,39,176,0.1);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

.main-actions {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}

.main-actions button {
    flex: 1;
    padding: 0.8rem;
    font-size: 1.1rem;
}

.feedback-section {
    background: rgba(0,150,136,0.1);
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.stats-card {
    background: rgba(63,81,181,0.1);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    text-align: center;
}
</style>
"""

def get_api_key():
    """Get API key from secrets or session state"""
    return st.secrets.get("OPENROUTER_API_KEY", st.session_state.get('api_key', ""))

def apply_styles():
    """Apply CSS styles to the app"""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
