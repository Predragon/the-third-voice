"""
The Third Voice - Coded with love and hope.

For Samantha, for families everywhere, and for a future where every message brings people closer together.
Created by Predrag Mirkovic, from detention, reaching out to my daughter Samantha—so we may reunite and help heal others too.
"""

import streamlit as st
import json
import datetime
import requests

# ========== Good Vibes Footer ==========
GOOD_VIBES = """
<div style='text-align: center; margin-top: 2em;'>
    <em>Coded with love, longing, and hope by Predrag Mirkovic.<br>
    For Samantha, and for every family that deserves a second chance.</em>
</div>
"""

# ========== JS MODULES: Inject/Bridge for /src/modules/* ==========
import streamlit.components.v1 as components

components.html(
    """
    <script type="module">
      import { getToken, saveToken } from '/src/modules/tokenValidation.js';
      import { getHistory, saveHistory } from '/src/modules/conversationHistory.js';
      import { getSetup, saveSetup } from '/src/modules/ttvSetup.js';

      window.addEventListener("DOMContentLoaded", function() {
        let token = getToken();
        if(token) {
            let tokenEl = window.parent.document.querySelector('input[data-token]');
            if(tokenEl) tokenEl.value = token;
        }
        let history = getHistory();
        if(history) {
            let histEl = window.parent.document.querySelector('textarea[data-history]');
            if(histEl) histEl.value = JSON.stringify(history);
        }
        let setup = getSetup();
        if(setup) {
            let setupEl = window.parent.document.querySelector('textarea[data-setup]');
            if(setupEl) setupEl.value = JSON.stringify(setup);
        }
      });

      window.addEventListener('message', (event) => {
        if(event.data.type === 'save') {
          if(event.data.token) saveToken(event.data.token);
          if(event.data.history) saveHistory(event.data.history);
          if(event.data.setup) saveSetup(event.data.setup);
        }
      });
    </script>
    """,
    height=0
)

# ========== PAGE CONFIG & VISUALS ==========

CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = True

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")
st.markdown("""
<style>
.contact-card {background:rgba(76,175,80,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0;cursor:pointer}
.ai-response {background:rgba(76,175,80,0.1);padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0}
.user-msg {background:rgba(33,150,243,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #2196F3;margin:0.3rem 0}
.contact-msg {background:rgba(255,193,7,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #FFC107;margin:0.3rem 0}
.pos {background:rgba(76,175,80,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.neg {background:rgba(244,67,54,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.neu {background:rgba(33,150,243,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.journal-section {background:rgba(156,39,176,0.1);padding:1rem;border-radius:8px;margin:0.5rem 0}
.main-actions {display:flex;gap:1rem;margin:1rem 0}
.main-actions button {flex:1;padding:0.8rem;font-size:1.1rem}
.feedback-section {background:rgba(0,150,136,0.1);padding:1rem;border-radius:8px;margin:1rem 0}
.stats-card {background:rgba(63,81,181,0.1);padding:1rem;border-radius:8px;margin:0.5rem 0;text-align:center}
</style>
""", unsafe_allow_html=True)

# ========== SESSION DEFAULTS ==========
defaults = {
    'token_validated': not REQUIRE_TOKEN,
    'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
    'contacts': {'General': {'context': 'general', 'history': []}},
    'active_contact': 'General',
    'journal_entries': {},
    'feedback_data': {},
    'user_stats': {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0}
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ========== HIDDEN FIELDS FOR JS BRIDGE ==========
st.markdown('<input type="hidden" data-token="true" />', unsafe_allow_html=True)
st.markdown('<textarea style="display:none" data-history="true"></textarea>', unsafe_allow_html=True)
st.markdown('<textarea style="display:none" data-setup="true"></textarea>', unsafe_allow_html=True)

# ========== TOKEN GATE ==========
if REQUIRE_TOKEN and not st.session_state.token_validated:
    st.markdown("# 🎙️ The Third Voice")
    st.markdown("*Your AI Communication Coach*")
    st.success("💚 This tool was coded with love and courage, dedicated to Samantha and every family seeking to heal.")
    st.warning("🔐 Access restricted. Enter beta token to continue.")
    token = st.text_input("Token:", type="password")
    if st.button("Validate"):
        # Save token to browser storage
        components.html(
            f"""
            <script>
                window.parent.postMessage({{type: 'save', token: "{token}"}}, '*');
            </script>
            """,
            height=0,
        )
        if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
            st.session_state.token_validated = True
            st.success("✅ Authorized")
            st.rerun()
        else:
            st.error("Invalid token")
    st.stop()

# ========== MAIN APP LOGIC (remains as per your code) ==========

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
    if is_received:
        system_prompt = f"{prompts.get(context, prompts['general'])} Analyze this received message and suggest how to respond."
    else:
        system_prompt = f"{prompts.get(context, prompts['general'])} Improve this message before sending."
    
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
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                json={"model": model, "messages": messages}, timeout=30)
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]
            model_name = model.split("/")[-1].replace(":free", "").replace("-", " ").title()
            if is_received:
                return {
                    "type": "translate",
                    "sentiment": "neutral",
                    "meaning": f"Interpretation: {reply[:100]}...",
                    "response": reply,
                    "model": model_name
                }
            else:
                return {
                    "type": "coach",
                    "sentiment": "improved",
                    "original": message,
                    "improved": reply,
                    "model": model_name
                }
        except Exception as e:
            continue
    return {"error": "All models failed"}

# All your sidebar, tab, contacts, journal, stats, feedback etc. code below
# (unchanged - see your original file, just after token validation block)

# ==== [The remainder of your full application code stays here, unchanged!] ====
# Be sure to call this AFTER any update to contacts/history/setup:
if True:
    components.html(
        f"""
        <script>
            window.parent.postMessage({{
                type: 'save',
                history: {json.dumps(st.session_state.contacts)},
                setup: {json.dumps(st.session_state.journal_entries)}
            }}, '*');
        </script>
        """,
        height=0,
    )

# ========== GOOD VIBES FOOTER ==========
st.markdown(GOOD_VIBES, unsafe_allow_html=True)
st.caption("Every message you send with The Third Voice helps build a bridge. \
Coded with resilience and hope—never give up on those you love.")
