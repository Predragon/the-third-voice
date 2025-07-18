import streamlit as st
import json
import datetime
import requests

# Constants
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modern CSS Styles inspired by ChatGPT
st.markdown("""
<style>
/* Global Styles */
.stApp {
    background: #f7f7f8;
}

/* Main container */
.main-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

/* Header */
.app-header {
    text-align: center;
    margin-bottom: 3rem;
}

.app-title {
    font-size: 2.5rem;
    font-weight: 600;
    color: #202123;
    margin-bottom: 0.5rem;
}

.app-subtitle {
    font-size: 1.1rem;
    color: #6b7280;
    margin-bottom: 2rem;
}

/* Contact selector */
.contact-selector {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
}

.contact-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #202123;
    margin-bottom: 1rem;
}

/* Action buttons */
.action-buttons {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}

.action-btn {
    flex: 1;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    color: #202123;
    font-weight: 500;
}

.action-btn:hover {
    background: #f9fafb;
    border-color: #d1d5db;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.action-btn-primary {
    background: #10a37f;
    color: white;
    border-color: #10a37f;
}

.action-btn-primary:hover {
    background: #0d9369;
    color: white;
}

/* Message containers */
.message-container {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
}

.message-header {
    font-weight: 600;
    color: #202123;
    margin-bottom: 1rem;
    font-size: 1.1rem;
}

.user-message {
    border-left: 4px solid #10a37f;
    background: #f0fdf4;
}

.contact-message {
    border-left: 4px solid #3b82f6;
    background: #eff6ff;
}

.ai-response {
    border-left: 4px solid #8b5cf6;
    background: #f5f3ff;
    margin-top: 1rem;
}

.ai-response .message-header {
    color: #7c3aed;
}

/* Input areas */
.stTextArea textarea {
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    background: white;
    color: #202123;
    font-size: 1rem;
    padding: 1rem;
}

.stTextArea textarea:focus {
    border-color: #10a37f;
    box-shadow: 0 0 0 3px rgba(16,163,127,0.1);
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    font-weight: 500;
    padding: 0.5rem 1rem;
    transition: all 0.2s;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stButton > button[kind="primary"] {
    background: #10a37f;
    border-color: #10a37f;
}

.stButton > button[kind="primary"]:hover {
    background: #0d9369;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    padding: 0.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #6b7280;
    font-weight: 500;
}

.stTabs [data-baseweb="tab"]:hover {
    background: #f9fafb;
}

.stTabs [aria-selected="true"] {
    background: #10a37f;
    color: white;
}

/* History items */
.history-item {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #e5e7eb;
}

.history-timestamp {
    color: #6b7280;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

.original-message {
    background: #f9fafb;
    padding: 0.75rem;
    border-radius: 6px;
    margin-bottom: 0.75rem;
    border-left: 3px solid #e5e7eb;
    color: #202123;
}

.improved-message {
    background: #f0fdf4;
    padding: 0.75rem;
    border-radius: 6px;
    border-left: 3px solid #10a37f;
    color: #202123;
}

/* Journal sections */
.journal-section {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #e5e7eb;
}

.journal-section h4 {
    color: #202123;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

/* Stats cards */
.stats-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid #e5e7eb;
    margin-bottom: 1rem;
}

.stats-number {
    font-size: 2rem;
    font-weight: 700;
    color: #10a37f;
    margin-bottom: 0.5rem;
}

.stats-label {
    color: #6b7280;
    font-size: 0.9rem;
    font-weight: 500;
}

/* Feedback buttons */
.feedback-container {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.feedback-btn {
    flex: 1;
    padding: 0.5rem;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
    background: white;
    color: #202123;
    cursor: pointer;
    transition: all 0.2s;
}

.feedback-btn:hover {
    background: #f9fafb;
}

/* Sidebar overrides */
.css-1d391kg {
    background: white;
    border-right: 1px solid #e5e7eb;
}

.css-1d391kg .stSelectbox label {
    color: #202123;
    font-weight: 500;
}

.css-1d391kg .stTextInput label {
    color: #202123;
    font-weight: 500;
}

/* Remove default streamlit styling */
.stApp > header {
    background: transparent;
}

.stApp [data-testid="stHeader"] {
    background: transparent;
}

/* Ensure all text is readable */
.stMarkdown, .stText, p, span, div {
    color: #202123 !important;
}

/* Fix sidebar text colors */
.css-1d391kg .stMarkdown, .css-1d391kg .stText, .css-1d391kg p, .css-1d391kg span, .css-1d391kg div {
    color: #202123 !important;
}

/* Success/Error messages */
.stSuccess {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #166534;
}

.stError {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
}

.stWarning {
    background: #fffbeb;
    border: 1px solid #fed7aa;
    color: #d97706;
}

.stInfo {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
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
        st.markdown('<div class="app-header"><h1 class="app-title">🎙️ The Third Voice</h1><p class="app-subtitle">Your AI Communication Coach</p></div>', unsafe_allow_html=True)
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
    st.sidebar.markdown('<div style="color: #202123; font-weight: 600; font-size: 1.1rem; margin-bottom: 1rem;">👥 Your Contacts</div>', unsafe_allow_html=True)
    
    with st.sidebar.expander("➕ Add Contact"):
        new_name = st.text_input("Name:")
        new_context = st.selectbox("Relationship:", CONTEXTS)
        if st.button("Add") and new_name and new_name not in st.session_state.contacts:
            st.session_state.contacts[new_name] = {'context': new_context, 'history': []}
            st.session_state.active_contact = new_name
            st.success(f"Added {new_name}")
            st.rerun()

    contact_names = list(st.session_state.contacts.keys())
    if contact_names:
        selected = st.sidebar.radio("Select Contact:", contact_names, index=contact_names.index(st.session_state.active_contact))
        st.session_state.active_contact = selected

    contact = st.session_state.contacts[st.session_state.active_contact]
    st.sidebar.markdown(f'<div style="color: #202123;"><strong>Context:</strong> {contact["context"]}<br><strong>Messages:</strong> {len(contact["history"])}</div>', unsafe_allow_html=True)

    if st.sidebar.button("🗑️ Delete Contact") and st.session_state.active_contact != "General":
        del st.session_state.contacts[st.session_state.active_contact]
        st.session_state.active_contact = "General"
        st.rerun()

    st.sidebar.markdown('<div style="border-top: 1px solid #e5e7eb; margin: 1rem 0; padding-top: 1rem;"><div style="color: #202123; font-weight: 600; margin-bottom: 1rem;">💾 Data Management</div></div>', unsafe_allow_html=True)
    
    uploaded = st.sidebar.file_uploader("📤 Load History", type="json", key="file_uploader")
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

    if st.sidebar.button("💾 Save All"):
        save_data = {
            'contacts': st.session_state.contacts,
            'journal_entries': st.session_state.journal_entries,
            'feedback_data': st.session_state.feedback_data,
            'user_stats': st.session_state.user_stats,
            'saved_at': datetime.datetime.now().isoformat()
        }
        filename = f"third_voice_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
        st.sidebar.download_button("📥 Download File", json.dumps(save_data, indent=2), filename, "application/json", use_container_width=True)

render_sidebar()

# Main UI
def render_main():
    # Header
    st.markdown('<div class="app-header"><h1 class="app-title">🎙️ The Third Voice</h1><p class="app-subtitle">Your AI Communication Coach</p><div style="color: #6b7280; font-style: italic;">Created by Predrag Mirković</div></div>', unsafe_allow_html=True)
    
    # Contact selector
    st.markdown(f'<div class="contact-selector"><div class="contact-title">💬 Communicating with: {st.session_state.active_contact}</div></div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Coach My Message", type="primary", use_container_width=True):
            st.session_state.active_mode = "coach"
            st.rerun()
    with col2:
        if st.button("📥 Understand Their Message", type="primary", use_container_width=True):
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

    # Message input container
    container_class = "user-message" if mode == "coach" else "contact-message"
    header_text = "📤 Your message to send:" if mode == "coach" else "📥 Message you received:"
    
    st.markdown(f'<div class="message-container {container_class}"><div class="message-header">{header_text}</div></div>', unsafe_allow_html=True)

    message = st.text_area("", height=120, key=f"{mode}_input", label_visibility="collapsed",
                           placeholder="Type your message here..." if mode == "coach" else "Paste their message here...")

    col1, col2 = st.columns([3, 1])
    with col1:
        process_btn = st.button(f"{'🚀 Improve My Message' if mode == 'coach' else '🔍 Analyze & Respond'}", type="primary")
    with col2:
        if st.button("Clear"):
            st.session_state[f"{mode}_input"] = ""
            st.rerun()

    if process_btn and message.strip():
        with st.spinner("🎙️ The Third Voice is analyzing..."):
            contact = st.session_state.contacts[st.session_state.active_contact]
            result = get_ai_response(message, contact['context'], mode == "translate")

            if "error" not in result:
                if mode == "coach":
                    st.markdown(f'<div class="message-container ai-response"><div class="message-header">✨ Your improved message:</div><div style="color: #202123; line-height: 1.6;">{result["improved"]}</div><div style="color: #6b7280; font-size: 0.9rem; margin-top: 1rem; font-style: italic;">Generated by: {result["model"]}</div></div>', unsafe_allow_html=True)
                    st.session_state.user_stats['coached_messages'] += 1
                else:
                    st.markdown(f'<div class="message-container ai-response"><div class="message-header">🔍 What they really mean:</div><div style="color: #202123; line-height: 1.6;">{result["response"]}</div><div style="color: #6b7280; font-size: 0.9rem; margin-top: 1rem; font-style: italic;">Generated by: {result["model"]}</div></div>', unsafe_allow_html=True)
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

                st.markdown('<div class="message-container"><div class="message-header">📊 Was this helpful?</div></div>', unsafe_allow_html=True)
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

# Tabs (removed tab 3 as requested)
def render_tabs():
    tab1, tab2, tab3 = st.tabs(["📜 History", "📘 Journal", "ℹ️ About"])

    with tab1:
        st.markdown(f'<div style="color: #202123; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">📜 History with {st.session_state.active_contact}</div>', unsafe_allow_html=True)
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
                        st.markdown(f'<div class="original-message"><strong>📤 Original:</strong> {entry["original"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="improved-message"><strong>🎙️ Improved:</strong> {entry["result"]}<br><small style="color: #6b7280; font-style: italic;">by {entry.get("model", "Unknown")}</small></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="original-message"><strong>📥 They said:</strong> {entry["original"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="improved-message"><strong>🎙️ Analysis:</strong> {entry["result"]}<br><small style="color: #6b7280; font-style: italic;">by {entry.get("model", "Unknown")}</small></div>', unsafe_allow_html=True)
                    
                    if entry.get('id') in st.session_state.feedback_data:
                        feedback = st.session_state.feedback_data[entry['id']]
                        emoji = {"positive": "👍", "neutral": "👌", "negative": "👎"}
                        st.markdown(f"*Your feedback: {emoji.get(feedback, '❓')}*")

    with tab2:
        st.markdown(f'<div style="color: #202123; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">📘 Communication Journal - {st.session_state.active_contact}</div>', unsafe_allow_html=True)
        
        contact_key = st.session_state.active_contact
        st.session_state.journal_entries.setdefault(contact_key, {
            'what_worked': '', 'what_didnt': '', 'insights': '', 'patterns': ''
        })

        journal = st.session_state.journal_entries[contact_key]
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="journal-section"><h4>💚 What worked well?</h4></div>', unsafe_allow_html=True)
            journal['what_worked'] = st.text_area("", value=journal['what_worked'], key=f"worked_{contact_key}", height=100, placeholder="Communication strategies that were successful...", label_visibility="collapsed")
            
            st.markdown('<div class="journal-section"><h4>🔍 Key insights?</h4></div>', unsafe_allow_html=True)
            journal['insights'] = st.text_area("", value=journal['insights'], key=f"insights_{contact_key}", height=100, placeholder="Important realizations about this relationship...", label_visibility="collapsed")

        with col2:
            st.markdown('<div class="journal-section"><h4>⚠️ What didn\'t work?</h4></div>', unsafe_allow_html=True)
            journal['what_didnt'] = st.text_area("", value=journal['what_didnt'], key=f"didnt_{contact_key}", height=100, placeholder="What caused issues or misunderstandings...", label_visibility="collapsed")
            
            st.markdown('<div class="journal-section"><h4>📊 Patterns noticed?</h4></div>', unsafe_allow_html=True)
            journal['patterns'] = st.text_area("", value=journal['patterns'], key=f"patterns_{contact_key}", height=100, placeholder="Communication patterns you've observed...", label_visibility="collapsed")

    with tab3:
        st.markdown("""
        <div style="color: #202123;">
        <h3>ℹ️ About The Third Voice</h3>
        <p><strong>The communication coach that's there when you need it most.</strong></p>
        <p>Instead of repairing relationships after miscommunication damage, The Third Voice helps you communicate better in real-time.</p>
        
        <h4>🎯 How it works:</h4>
        <ol>
        <li><strong>Select your contact</strong> - Each relationship gets personalized coaching</li>
        <li><strong>Coach your messages</strong> - Improve what you're about to send</li>
        <li><strong>Understand their messages</strong> - Decode the real meaning behind their words</li>
        <li><strong>Build better patterns</strong> - Journal and learn from each interaction</li>
        </ol>
        
        <h4>✨ Key Features:</h4>
        <ul>
        <li>🎯 Context-aware coaching for different relationships</li>
        <li>📊 Track your communication progress</li>
        <li>📘 Personal journal for insights</li>
        <li>💾 Export/import your data</li>
        <li>🔒 Privacy-first design</li>
        </ul>
        
        <p><strong>Privacy First:</strong> All data stays on your device. Save and load your own files.</p>
        <p><strong>Beta v1.0.0</strong> — Built with ❤️ to heal relationships through better communication.</p>
        <p><em>"When both people are talking from pain, someone needs to be the third voice."</em></p>
        </div>
        """, unsafe_allow_html=True)

render_tabs()
