import streamlit as st
import json
import datetime
import requests

# Constants
CONTEXTS = ["romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# CSS Styles
st.markdown("""
<style>
/* Main Layout */
[data-testid="stSidebar"] {
    background: #f7f7f8 !important;
    border-right: 1px solid #e5e5e6;
}
[data-testid="stSidebarUserContent"] {
    padding: 1rem;
}
[data-testid="stAppViewContainer"] {
    background: white;
}
[data-testid="stHeader"] {
    background: white;
    border-bottom: 1px solid #e5e5e6;
}

/* Chat Elements */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}
.user-message {
    background: #f7f7f8;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border: 1px solid #e5e5e6;
}
.ai-message {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border: 1px solid #e5e5e6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.message-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: black !important;
}
.message-content {
    line-height: 1.5;
    color: black !important;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    padding: 0.5rem 1rem;
    border: 1px solid #e5e5e6;
    background: white;
    color: black !important;
}
.stButton>button:hover {
    background: #f7f7f8;
}
.primary-button {
    background: #19c37d !important;
    color: white !important;
    border: none !important;
}
.primary-button:hover {
    background: #16a369 !important;
    color: white !important;
}

/* Input */
.stTextArea>div>div>textarea {
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #e5e5e6;
    color: black !important;
}
.stTextArea>div>div>textarea:focus {
    border-color: #19c37d;
    box-shadow: 0 0 0 2px rgba(25,195,125,0.1);
}

/* Sidebar Elements */
.sidebar-item {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    margin: 0.25rem 0;
    cursor: pointer;
    color: black !important;
}
.sidebar-item:hover {
    background: #e5e5e6;
}
.sidebar-item.active {
    background: #e5e5e6;
    font-weight: 600;
}
.sidebar-section {
    margin: 1rem 0;
}
.sidebar-section-title {
    font-size: 0.85rem;
    text-transform: uppercase;
    color: #6e6e80;
    margin-bottom: 0.5rem;
    padding: 0 1rem;
}

/* Tabs */
[data-testid="stTab"] {
    border-bottom: 1px solid #e5e5e6;
}
[data-testid="stTab"] button {
    padding: 0.5rem 1rem;
    border-radius: 8px 8px 0 0;
    color: black !important;
}
[data-testid="stTab"] button:hover {
    background: #f7f7f8;
}
[data-testid="stTab"] button[aria-selected="true"] {
    background: white;
    border-color: #e5e5e6;
    border-bottom-color: white;
    font-weight: 600;
    color: black !important;
}

/* Stats Cards */
.stats-card {
    background: white;
    border: 1px solid #e5e5e6;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    margin: 0.5rem 0;
    color: black !important;
}
.stats-number {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
    color: black !important;
}
.stats-label {
    font-size: 0.85rem;
    color: #6e6e80;
}

/* Journal Entries */
.journal-section {
    background: white;
    border: 1px solid #e5e5e6;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    color: black !important;
}
.journal-title {
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: black !important;
}

/* Header elements */
[data-testid="stToolbar"] {
    visibility: visible !important;
}
[data-testid="stDecoration"] {
    visibility: visible !important;
}
[data-testid="baseButton-header"] {
    visibility: visible !important;
}

/* Force light theme but keep header elements */
[data-testid="stAppViewContainer"] {
    background-color: white !important;
    color: black !important;
}
[data-testid="stHeader"] {
    background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize Session State
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
        'contacts': {'General': {'context': 'general', 'history': []}},
        'active_contact': 'General',
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
        st.markdown("""
        <div class="chat-container">
            <h1 style="text-align: center; margin-bottom: 1rem;">🎙️ The Third Voice</h1>
            <p style="text-align: center; color: #6e6e80; margin-bottom: 2rem;">Your AI Communication Coach</p>
            <div class="ai-message">
                <div style="text-align: center; margin-bottom: 1rem;">
                    🔐 Access restricted. Enter beta token to continue.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            token = st.text_input("Token:", type="password", label_visibility="collapsed")
            if st.button("Validate", type="primary", use_container_width=True):
                if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
                    st.session_state.token_validated = True
                    st.rerun()
                else:
                    st.error("Invalid token")
        st.stop()

validate_token()

# API Interaction
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

# Sidebar: Contact Management
def render_sidebar():
    st.sidebar.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        <h1 style="margin: 0;">🎙️</h1>
        <div style="margin-left: 0.5rem;">
            <div style="font-weight: 600; color: black;">Third Voice</div>
            <div style="font-size: 0.8rem; color: #6e6e80;">Communication Coach</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar.expander("➕ New Chat", expanded=False):
        new_name = st.text_input("Contact Name:", key="new_contact_name")
        new_context = st.selectbox("Relationship:", CONTEXTS, key="new_contact_context")
        if st.button("Create", key="create_contact", type="primary"):
            if new_name and new_name not in st.session_state.contacts:
                st.session_state.contacts[new_name] = {'context': new_context, 'history': []}
                st.session_state.active_contact = new_name
                st.rerun()

    st.sidebar.markdown('<div class="sidebar-section-title">Your Conversations</div>', unsafe_allow_html=True)
    
    contact_names = list(st.session_state.contacts.keys())
    for name in contact_names:
        active_class = "active" if name == st.session_state.active_contact else ""
        st.sidebar.markdown(
            f'<div class="sidebar-item {active_class}" onclick="window.streamlitScriptRunner.handleScriptRun(\'set_contact\', \'{name}\')">{name}</div>',
            unsafe_allow_html=True
        )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="sidebar-section-title">Tools</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("📤 Export Data", use_container_width=True):
        save_data = {
            'contacts': st.session_state.contacts,
            'journal_entries': st.session_state.journal_entries,
            'feedback_data': st.session_state.feedback_data,
            'user_stats': st.session_state.user_stats,
            'saved_at': datetime.datetime.now().isoformat()
        }
        filename = f"third_voice_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
        st.sidebar.download_button("📥 Download", json.dumps(save_data, indent=2), filename, "application/json", use_container_width=True)
    
    uploaded = st.sidebar.file_uploader("📥 Import Data", type="json", label_visibility="collapsed")
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.contacts = data.get('contacts', {'General': {'context': 'general', 'history': []}})
            st.session_state.journal_entries = data.get('journal_entries', {})
            st.session_state.feedback_data = data.get('feedback_data', {})
            st.session_state.user_stats = data.get('user_stats', {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0})
            if st.session_state.active_contact not in st.session_state.contacts:
                st.session_state.active_contact = "General"
            st.sidebar.success("✅ Data loaded!")
            st.session_state['file_uploader'] = None
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Invalid file: {str(e)}")

# Main Chat Interface
def render_chat_interface():
    st.markdown(f"""
    <div class="chat-container">
        <div style="text-align: center; margin-bottom: 1rem;">
            <h3 style="color: black;">💬 {st.session_state.active_contact}</h3>
            <p style="color: #6e6e80; font-size: 0.9rem;">
                {st.session_state.contacts[st.session_state.active_contact]['context'].title()} context
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Improve My Message", type="primary", use_container_width=True):
            st.session_state.active_mode = "coach"
            st.rerun()
    with col2:
        if st.button("📥 Analyze Their Message", type="primary", use_container_width=True):
            st.session_state.active_mode = "translate"
            st.rerun()
    
    contact = st.session_state.contacts[st.session_state.active_contact]
    if contact['history']:
        st.markdown('<div class="sidebar-section-title">Recent Messages</div>', unsafe_allow_html=True)
        for entry in reversed(contact['history'][-3:]):  # Show last 3 messages
            if entry['type'] == 'coach':
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-header">📤 You</div>
                    <div class="message-content">{entry["original"][:100]}...</div>
                </div>
                <div class="ai-message">
                    <div class="message-header">🎙️ Improved Version</div>
                    <div class="message-content">{entry["result"][:150]}...</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-header">📥 They said</div>
                    <div class="message-content">{entry["original"][:100]}...</div>
                </div>
                <div class="ai-message">
                    <div class="message-header">🎙️ Analysis</div>
                    <div class="message-content">{entry["result"][:150]}...</div>
                </div>
                """, unsafe_allow_html=True)

# Message Processing
def render_message_input():
    if not st.session_state.active_mode:
        return

    mode = st.session_state.active_mode
    if st.button("← Back"):
        st.session_state.active_mode = None
        st.rerun()

    st.markdown(f"""
    <div class="chat-container">
        <div class="{'user-message' if mode == 'coach' else 'ai-message'}">
            <div class="message-header">{"📤 Your message to send" if mode == 'coach' else "📥 Message you received"}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    message = st.text_area("", height=120, key=f"{mode}_input", label_visibility="collapsed",
                         placeholder="Type your message here..." if mode == "coach" else "Paste their message here...")

    col1, col2 = st.columns([3, 1])
    with col1:
        process_btn = st.button(f"{'🚀 Improve My Message' if mode == 'coach' else '🔍 Analyze & Respond'}", type="primary")
    with col2:
        if st.button("Clear", type="secondary"):
            st.session_state[f"{mode}_input"] = ""
            st.rerun()

    if process_btn and message.strip():
        with st.spinner("🎙️ The Third Voice is analyzing..."):
            contact = st.session_state.contacts[st.session_state.active_contact]
            result = get_ai_response(message, contact['context'], mode == "translate")

            if "error" not in result:
                st.markdown("""
                <div class="chat-container">
                    <div class="ai-message">
                        <div class="message-header">🎙️ The Third Voice</div>
                """, unsafe_allow_html=True)
                
                if mode == "coach":
                    st.markdown(f"""
                        <div class="message-content">
                            <p><strong>✨ Your improved message:</strong></p>
                            <p>{result["improved"]}</p>
                            <p style="font-size: 0.8rem; color: #6e6e80; margin-top: 1rem;">
                                Generated by: {result["model"]}
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.user_stats['coached_messages'] += 1
                else:
                    st.markdown(f"""
                        <div class="message-content">
                            <p><strong>🔍 What they really mean:</strong></p>
                            <p>{result["response"]}</p>
                            <p style="font-size: 0.8rem; color: #6e6e80; margin-top: 1rem;">
                                Generated by: {result["model"]}
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
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

                st.markdown("""
                <div class="chat-container">
                    <div style="text-align: center; margin: 1rem 0;">
                        <p style="color: black;">Was this helpful?</p>
                        <div style="display: flex; gap: 0.5rem; justify-content: center;">
                """, unsafe_allow_html=True)
                
                for label, emoji in [("Yes", "👍"), ("Okay", "👌"), ("No", "👎")]:
                    if st.button(emoji, key=f"{emoji}_{history_entry['id']}"):
                        feedback_value = {"👍": "positive", "👌": "neutral", "👎": "negative"}[emoji]
                        st.session_state.feedback_data[history_entry['id']] = feedback_value
                        st.success("Thanks for the feedback!")
                
                st.markdown("</div></div></div>", unsafe_allow_html=True)
                st.success("✅ Saved to history")
            else:
                st.error(f"❌ {result['error']}")
    elif process_btn:
        st.warning("⚠️ Please enter a message first.")

# Tabs
def render_tabs():
    tab1, tab2, tab3 = st.tabs(["📜 History", "📘 Journal", "📊 Stats"])

    with tab1:
        st.markdown(f"### History with {st.session_state.active_contact}")
        contact = st.session_state.contacts[st.session_state.active_contact]
        if not contact['history']:
            st.info(f"No messages yet with {st.session_state.active_contact}. Use the buttons above to get started!")
        else:
            filter_type = st.selectbox("Filter:", ["All", "Coached Messages", "Understood Messages"])
            filtered_history = contact['history']
            if filter_type == "Coached Messages":
                filtered_history = [h for h in contact['history'] if h['type'] == 'coach']
            elif filter_type == "Understood Messages":
                filtered_history = [h for h in contact['history'] if h['type'] == 'translate']

            for entry in reversed(filtered_history):
                with st.expander(f"**{entry['time']}** • {entry['type'].title()} • {entry['original'][:50]}..."):
                    if entry['type'] == 'coach':
                        st.markdown(f"""
                        <div class="user-message">
                            <div class="message-header">📤 Original</div>
                            <div class="message-content">{entry["original"]}</div>
                        </div>
                        <div class="ai-message">
                            <div class="message-header">🎙️ Improved</div>
                            <div class="message-content">{entry["result"]}</div>
                            <div style="font-size: 0.8rem; color: #6e6e80; margin-top: 0.5rem;">
                                by {entry.get("model", "Unknown")}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="user-message">
                            <div class="message-header">📥 They said</div>
                            <div class="message-content">{entry["original"]}</div>
                        </div>
                        <div class="ai-message">
                            <div class="message-header">🎙️ Analysis</div>
                            <div class="message-content">{entry["result"]}</div>
                            <div style="font-size: 0.8rem; color: #6e6e80; margin-top: 0.5rem;">
                                by {entry.get("model", "Unknown")}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if entry.get('id') in st.session_state.feedback_data:
                        feedback = st.session_state.feedback_data[entry['id']]
                        emoji = {"positive": "👍", "neutral": "👌", "negative": "👎"}
                        st.markdown(f"*Your feedback: {emoji.get(feedback, '❓')}*")

    with tab2:
        st.markdown(f"### Communication Journal - {st.session_state.active_contact}")
        contact_key = st.session_state.active_contact
        st.session_state.journal_entries.setdefault(contact_key, {
            'what_worked': '', 'what_didnt': '', 'insights': '', 'patterns': ''
        })

        journal = st.session_state.journal_entries[contact_key]
        
        st.markdown("""
        <div class="journal-section">
            <div class="journal-title">💚 What worked well?</div>
        </div>
        """, unsafe_allow_html=True)
        journal['what_worked'] = st.text_area("", value=journal['what_worked'], key=f"worked_{contact_key}", height=100, label_visibility="collapsed")
        
        st.markdown("""
        <div class="journal-section">
            <div class="journal-title">⚠️ What didn't work?</div>
        </div>
        """, unsafe_allow_html=True)
        journal['what_didnt'] = st.text_area("", value=journal['what_didnt'], key=f"didnt_{contact_key}", height=100, label_visibility="collapsed")
        
        st.markdown("""
        <div class="journal-section">
            <div class="journal-title">🔍 Key insights?</div>
        </div>
        """, unsafe_allow_html=True)
        journal['insights'] = st.text_area("", value=journal['insights'], key=f"insights_{contact_key}", height=100, label_visibility="collapsed")
        
        st.markdown("""
        <div class="journal-section">
            <div class="journal-title">📊 Patterns noticed?</div>
        </div>
        """, unsafe_allow_html=True)
        journal['patterns'] = st.text_area("", value=journal['patterns'], key=f"patterns_{contact_key}", height=100, label_visibility="collapsed")

    with tab3:
        st.markdown("### Your Communication Stats")
        col1, col2, col3 = st.columns(3)
        for idx, (stat, label) in enumerate([
            (st.session_state.user_stats["total_messages"], "Total Messages"),
            (st.session_state.user_stats["coached_messages"], "Messages Coached"),
            (st.session_state.user_stats["translated_messages"], "Messages Understood")
        ]):
            with [col1, col2, col3][idx]:
                st.markdown(f"""
                <div class="stats-card">
                    <div class="stats-number">{stat}</div>
                    <div class="stats-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### By Contact")
        for name, contact in st.session_state.contacts.items():
            if contact['history']:
                coached = sum(1 for h in contact['history'] if h['type'] == 'coach')
                translated = sum(1 for h in contact['history'] if h['type'] == 'translate')
                st.markdown(f"""
                <div class="ai-message" style="margin-bottom: 0.5rem;">
                    <div style="font-weight: 600; color: black;">{name}</div>
                    <div style="font-size: 0.9rem; color: #6e6e80;">
                        {len(contact['history'])} total • {coached} coached • {translated} understood
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if st.session_state.feedback_data:
            st.markdown("### Feedback Summary")
            feedback_counts = {
                "positive": sum(1 for f in st.session_state.feedback_data.values() if f == "positive"),
                "neutral": sum(1 for f in st.session_state.feedback_data.values() if f == "neutral"),
                "negative": sum(1 for f in st.session_state.feedback_data.values() if f == "negative")
            }
            st.markdown(f"""
            <div style="display: flex; gap: 1rem; justify-content: center;">
                <div style="text-align: center;">
                    <div style="font-size: 1.2rem;">👍</div>
                    <div>{feedback_counts['positive']}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.2rem;">👌</div>
                    <div>{feedback_counts['neutral']}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.2rem;">👎</div>
                    <div>{feedback_counts['negative']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Main App Layout
def main():
    render_sidebar()
    
    if not st.session_state.active_mode:
        render_chat_interface()
    else:
        render_message_input()
    
    render_tabs()

if __name__ == "__main__":
    main()
