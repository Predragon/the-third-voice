import streamlit as st
import json
import datetime
import requests

# Constants
CONTEXTS = ["romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# CSS Styles (Cleaner, no red tones)
st.markdown("""
<style>
.contact-card {background:rgba(76,175,80,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0;cursor:pointer}
.ai-response {background:rgba(76,175,80,0.1);padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0}
.user-msg {background:rgba(33,150,243,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #2196F3;margin:0.3rem 0}
.contact-msg {background:rgba(255,193,7,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #FFC107;margin:0.3rem 0}
.pos {background:rgba(76,175,80,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.neu {background:rgba(33,150,243,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.journal-section {background:rgba(156,39,176,0.1);padding:1rem;border-radius:8px;margin:0.5rem 0}
.main-actions {display:flex;gap:1rem;margin:1rem 0}
.main-actions button {flex:1;padding:0.8rem;font-size:1.1rem}
.feedback-section {background:rgba(0,150,136,0.1);padding:1rem;border-radius:8px;margin:1rem 0}
</style>
""", unsafe_allow_html=True)

# Initialize Session State
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
        'contacts': {context: {'context': context, 'history': []} for context in CONTEXTS},
        'active_contact': CONTEXTS[0],
        'journal_entries': {},
        'feedback_data': {},
        'user_stats': {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0},
        'active_mode': None
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

initialize_session()

# Token Validation
def validate_token():
    if REQUIRE_TOKEN and not st.session_state.token_validated:
        st.markdown("# 🎙️ The Third Voice\n*Your AI Communication Coach*")
        st.warning("🔐 Access restricted. Enter beta token to continue.")
        token = st.text_input("Token:", type="password")
        if st.button("Validate"):
            if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
                st.session_state.token_validated = True
                st.success("✅ Authorized")
                st.rerun()
            else:
                st.error("Invalid token")
        st.stop()

validate_token()

# API Interaction with Rate Limit Fallback
def get_ai_response(message, context, is_received=False):
    if not st.session_state.api_key:
        return {"error": "No API key"}

    prompts = {
    "romantic": "You are an emotionally intelligent communication coach specializing in romantic relationships. We are responding to my partner. Strictly reframe this message with empathy, clarity, and intimacy, avoiding blame or narrative detours, and always suggest a positive next step to maintain connection. Do not generate stories or ask for additional context.",
    "coparenting": "You offer emotionally safe responses for coparenting focused on the children's wellbeing.",
    "workplace": "You translate workplace messages for professional tone and clear intent.",
    "family": "You understand family dynamics and help rephrase for better family relationships.",
    "friend": "You assist with friendship communication to strengthen bonds and resolve conflicts."
    }

    system_prompt = f"{prompts.get(context, prompts['family'])} {'Analyze this received message and suggest how to respond.' if is_received else 'Improve this message before sending.'}"

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
        except Exception as e:
            continue

    # Fallback for rate limit or API issues
    return {"error": "API limit reached. Please try again later or contact hello@thethirdvoice.ai for support."}

# Sidebar: Context Management
def render_sidebar():
    st.sidebar.markdown("### 👥 Your Contexts")
    with st.sidebar.expander("➕ Add Custom Contact"):
        new_name = st.text_input("Name:")
        new_context = st.selectbox("Relationship:", CONTEXTS)
        if st.button("Add") and new_name and new_name not in st.session_state.contacts:
            st.session_state.contacts[new_name] = {'context': new_context, 'history': []}
            st.session_state.active_contact = new_name
            st.success(f"Added {new_name}")
            st.rerun()

    contact_names = list(st.session_state.contacts.keys())
    if contact_names:
        selected = st.sidebar.radio("Select Context:", contact_names, index=contact_names.index(st.session_state.active_contact))
        st.session_state.active_contact = selected

    contact = st.session_state.contacts[st.session_state.active_contact]
    st.sidebar.markdown(f"**Context:** {contact['context']}\n**Messages:** {len(contact['history'])}")

    if st.sidebar.button("🗑️ Delete Contact") and st.session_state.active_contact not in CONTEXTS:
        del st.session_state.contacts[st.session_state.active_contact]
        st.session_state.active_contact = CONTEXTS[0]
        st.rerun()

    st.sidebar.markdown("---\n### 💾 Data Management")
    uploaded = st.sidebar.file_uploader("📤 Load History", type="json", key="file_uploader")
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.contacts = data.get('contacts', {context: {'context': context, 'history': []} for context in CONTEXTS})
            st.session_state.journal_entries = data.get('journal_entries', {})
            st.session_state.feedback_data = data.get('feedback_data', {})
            if st.session_state.active_contact not in st.session_state.contacts:
                st.session_state.active_contact = CONTEXTS[0]
            st.sidebar.success("✅ Data loaded!")
            st.session_state['file_uploader'] = None
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Invalid file: {str(e)}")

    if st.sidebar.button("💾 Save All"):
        save_data = {
            'contacts': st.session_state.contacts,
            'journal_entries': st.session_state.journal_entries,
            'feedback_data': st.session_state.feedback_data,
            'saved_at': datetime.datetime.now().isoformat()
        }
        filename = f"third_voice_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
        st.sidebar.download_button("📥 Download File", json.dumps(save_data, indent=2), filename, "application/json", use_container_width=True)

render_sidebar()

# Main UI
def render_main():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.svg")
        except:
            st.markdown("# 🎙️ The Third Voice")
        st.markdown("<div style='text-align: center'><i>Built for families</i></div>", unsafe_allow_html=True)

    st.markdown(f"### 💬 Context: **{st.session_state.active_contact}**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Refine My Words", type="primary", use_container_width=True):
            st.session_state.active_mode = "coach"
            st.rerun()
    with col2:
        if st.button("📥 Decode Their Heart", type="primary", use_container_width=True):
            st.session_state.active_mode = "translate"
            st.rerun()

render_main()

# Message Processing
def render_message_input():
    if not st.session_state.active_mode:
        return

    mode = st.session_state.active_mode
    if st.button("← Back"):
        st.session_state.active_mode = None
        st.rerun()

    input_class = "user-msg" if mode == "coach" else "contact-msg"
    st.markdown(f'<div class="{input_class}"><strong>{"📤 Your message to send:" if mode == "coach" else "📥 Message you received:"}</strong></div>', unsafe_allow_html=True)

    message = st.text_area("", height=120, key=f"{mode}_input", label_visibility="collapsed",
                           placeholder="Type your message here..." if mode == "coach" else "Paste their message here...")

    col1, col2 = st.columns([3, 1])
    with col1:
        process_btn = st.button(f"{'🚀 Refine My Words' if mode == 'coach' else '🔍 Decode Their Heart'}", type="secondary")
    with col2:
        if st.button("Clear", type="secondary"):
            st.session_state[f"{mode}_input"] = ""
            st.rerun()

    if process_btn and message.strip():
        with st.spinner("🎙️ The Third Voice is analyzing..."):
            contact = st.session_state.contacts[st.session_state.active_contact]
            result = get_ai_response(message, contact['context'], mode == "translate")

            if "error" not in result:
                st.markdown("### 🎙️ The Third Voice says:")
                if mode == "coach":
                    st.markdown(f'<div class="ai-response"><strong>✨ Your refined message:</strong><br><br>{result["improved"]}<br><br><small><i>Generated by: {result["model"]}</i></small></div>', unsafe_allow_html=True)
                    st.session_state.user_stats['coached_messages'] += 1
                else:
                    st.markdown(f'<div class="ai-response"><strong>🔍 What they truly mean:</strong><br>{result["response"]}<br><br><small><i>Generated by: {result["model"]}</i></small></div>', unsafe_allow_html=True)
                    st.session_state.user_stats['translated_messages'] += 1

                history_entry = {
                    "id": f"{mode}_{len(contact['history'])}_{datetime.datetime.now().timestamp()}",
                    "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                    "type": mode,
                    "original": message,
                    "result": result.get("improved" if mode == "coach" else "response", ""),
                    "sentiment": result.get("sentiment", "neutral"),
                    "model": result.get("model", "Unknown")
                }

                contact['history'].append(history_entry)
                st.session_state.user_stats['total_messages'] += 1

                st.markdown("### 📊 Was this helpful?")
                col1, col2, col3 = st.columns(3)
                for idx, (label, emoji) in enumerate([("👍 Yes", "positive"), ("👌 Okay", "neutral"), ("👎 No", "negative")]):
                    with [col1, col2, col3][idx]:
                        if st.button(label, key=f"{emoji}_{history_entry['id']}"):
                            st.session_state.feedback_data[history_entry['id']] = emoji
                            st.success("Thanks for the feedback!")

                st.success("✅ Saved to history")
            else:
                st.error(f"❌ {result['error']}")
    elif process_btn:
        st.warning("⚠️ Please enter a message first.")

render_message_input()

# Tabs
def render_tabs():
    tab1, tab2, tab4 = st.tabs(["📜 History", "📘 Journal", "ℹ️ About"])

    with tab1:
        st.markdown(f"### 📜 History with {st.session_state.active_contact}")
        contact = st.session_state.contacts[st.session_state.active_contact]
        if not contact['history']:
            st.info(f"No messages yet with {st.session_state.active_contact}. Use the buttons above to get started!")
        else:
            filter_type = st.selectbox("Filter:", ["All", "Refined Messages", "Decoded Messages"])
            filtered_history = contact['history']
            if filter_type == "Refined Messages":
                filtered_history = [h for h in contact['history'] if h['type'] == 'coach']
            elif filter_type == "Decoded Messages":
                filtered_history = [h for h in contact['history'] if h['type'] == 'translate']

            for entry in reversed(filtered_history):
                with st.expander(f"**{entry['time']}** • {entry['type'].title()} • {entry['original'][:50]}..."):
                    if entry['type'] == 'coach':
                        st.markdown(f'<div class="user-msg">📤 <strong>Original:</strong> {entry["original"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="ai-response">🎙️ <strong>Refined:</strong> {entry["result"]}<br><small><i>by {entry.get("model", "Unknown")}</i></small></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="contact-msg">📥 <strong>They said:</strong> {entry["original"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="ai-response">🎙️ <strong>Decoded:</strong> {entry["result"]}<br><small><i>by {entry.get("model", "Unknown")}</i></small></div>', unsafe_allow_html=True)
                    if entry.get('id') in st.session_state.feedback_data:
                        feedback = st.session_state.feedback_data[entry['id']]
                        emoji = {"positive": "👍", "neutral": "👌", "negative": "👎"}
                        st.markdown(f"*Your feedback: {emoji.get(feedback, '❓')}*")

    with tab2:
        st.markdown(f"### 📘 Communication Journal - {st.session_state.active_contact}")
        contact_key = st.session_state.active_contact
        st.session_state.journal_entries.setdefault(contact_key, {
            'what_worked': '', 'what_didnt': '', 'insights': '', 'patterns': ''
        })

        journal = st.session_state.journal_entries[contact_key]
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="journal-section">**💚 What worked well?**</div>', unsafe_allow_html=True)
            journal['what_worked'] = st.text_area("", value=journal['what_worked'], key=f"worked_{contact_key}", height=100, placeholder="Communication strategies that were successful...")
            st.markdown('<div class="journal-section">**🔍 Key insights?**</div>', unsafe_allow_html=True)
            journal['insights'] = st.text_area("", value=journal['insights'], key=f"insights_{contact_key}", height=100, placeholder="Important realizations about this relationship...")

        with col2:
            st.markdown('<div class="journal-section">**⚠️ What didn’t work?**</div>', unsafe_allow_html=True)
            journal['what_didnt'] = st.text_area("", value=journal['what_didnt'], key=f"didnt_{contact_key}", height=100, placeholder="What caused issues or misunderstandings...")
            st.markdown('<div class="journal-section">**📊 Patterns noticed?**</div>', unsafe_allow_html=True)
            journal['patterns'] = st.text_area("", value=journal['patterns'], key=f"patterns_{contact_key}", height=100, placeholder="Communication patterns you've observed...")

    with tab4:
        st.markdown("""
        ### ℹ️ About The Third Voice
        **The communication coach born from love and struggle.**
        Founded by Predrag Mirković during his fight to reunite with his daughter Samantha, The Third Voice heals families through better communication. Visit us at [thethirdvoice.ai](https://thethirdvoice.ai) or email [hello@thethirdvoice.ai](mailto:hello@thethirdvoice.ai).
        **How it works:**
        1. **Select your context** - Personalized coaching for every relationship
        2. **Refine your words** - Improve what you send
        3. **Decode their heart** - Understand the meaning behind their messages
        4. **Build better patterns** - Journal to strengthen family bonds
        **Key Features:**
        - 🎯 Context-aware coaching for real-life relationships
        - 📘 Personal journal for insights
        - 💾 Export/import your data
        - 🔒 Privacy-first design
        **Privacy First:** All data stays on your device.
        **Beta v1.0.0** — Built with ❤️ to reunite families.
        *"When both people are talking from pain, someone needs to be the third voice."*
        ---
        **Join the Movement:**
        - 💻 Contribute on [GitHub](https://github.com/thethirdvoice)
        - 📧 Suggest features or report bugs
        - 🌟 Share your family stories
        **Technical Details:**
        - Powered by OpenRouter API
        - Built with Streamlit on an Android phone
        """)

render_tabs()
