import streamlit as st
import json
import datetime
import requests
from typing import Dict, List, Optional, Any

# Constants
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False
VALID_TOKENS = ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]

# CSS Styles
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
.journal-section {
    background: rgba(156,39,176,0.1);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
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

# AI Model Configuration
AI_MODELS = [
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free"
]

# Prompts for different contexts
CONTEXT_PROMPTS = {
    "general": "You are an emotionally intelligent communication coach. Help improve this message for clarity and empathy.",
    "romantic": "You help reframe romantic messages with empathy and clarity while maintaining intimacy.",
    "coparenting": "You offer emotionally safe responses for coparenting focused on the children's wellbeing.",
    "workplace": "You translate workplace messages for professional tone and clear intent.",
    "family": "You understand family dynamics and help rephrase for better family relationships.",
    "friend": "You assist with friendship communication to strengthen bonds and resolve conflicts."
}


def setup_page():
    """Configure Streamlit page settings and apply CSS."""
    st.set_page_config(
        page_title="The Third Voice",
        page_icon="🎙️",
        layout="wide"
    )
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state with default values."""
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
        'contacts': {'General': {'context': 'general', 'history': []}},
        'active_contact': 'General',
        'journal_entries': {},
        'feedback_data': {},
        'user_stats': {
            'total_messages': 0,
            'coached_messages': 0,
            'translated_messages': 0
        },
        'active_mode': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_token():
    """Handle token validation for restricted access."""
    if not REQUIRE_TOKEN or st.session_state.token_validated:
        return True
    
    st.markdown("# 🎙️ The Third Voice")
    st.markdown("*Your AI Communication Coach*")
    st.warning("🔐 Access restricted. Enter beta token to continue.")
    
    token = st.text_input("Token:", type="password")
    if st.button("Validate"):
        if token in VALID_TOKENS:
            st.session_state.token_validated = True
            st.success("✅ Authorized")
            st.rerun()
        else:
            st.error("Invalid token")
    
    return False


def get_ai_response(message: str, context: str, is_received: bool = False) -> Dict[str, Any]:
    """Get AI response for message coaching or translation."""
    if not st.session_state.api_key:
        return {"error": "No API key configured"}
    
    system_prompt = CONTEXT_PROMPTS.get(context, CONTEXT_PROMPTS['general'])
    if is_received:
        system_prompt += " Analyze this received message and suggest how to respond."
    else:
        system_prompt += " Improve this message before sending."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Message: {message}"}
    ]
    
    for model in AI_MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                json={"model": model, "messages": messages},
                timeout=30
            )
            response.raise_for_status()
            
            reply = response.json()["choices"][0]["message"]["content"]
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
    
    return {"error": "All AI models failed to respond"}


def render_sidebar():
    """Render the sidebar with contact management and data controls."""
    st.sidebar.markdown("### 👥 Your Contacts")
    
    # Add new contact section
    with st.sidebar.expander("➕ Add Contact"):
        new_name = st.text_input("Name:")
        new_context = st.selectbox("Relationship:", CONTEXTS)
        
        if st.button("Add") and new_name and new_name not in st.session_state.contacts:
            st.session_state.contacts[new_name] = {
                'context': new_context,
                'history': []
            }
            st.session_state.active_contact = new_name
            st.success(f"Added {new_name}")
            st.rerun()
    
    # Contact selection
    contact_names = list(st.session_state.contacts.keys())
    if contact_names:
        selected = st.sidebar.radio(
            "Select Contact:",
            contact_names,
            index=contact_names.index(st.session_state.active_contact)
        )
        st.session_state.active_contact = selected
    
    # Contact info display
    if st.session_state.active_contact in st.session_state.contacts:
        contact = st.session_state.contacts[st.session_state.active_contact]
        st.sidebar.markdown(f"**Context:** {contact['context']}")
        st.sidebar.markdown(f"**Messages:** {len(contact['history'])}")
    
    # Delete contact button
    if (st.sidebar.button("🗑️ Delete Contact") and 
        st.session_state.active_contact != "General"):
        del st.session_state.contacts[st.session_state.active_contact]
        st.session_state.active_contact = "General"
        st.rerun()
    
    # Data management section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Data Management")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader("📤 Load History", type="json")
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.session_state.contacts = data.get('contacts', st.session_state.contacts)
            st.session_state.journal_entries = data.get('journal_entries', {})
            st.session_state.feedback_data = data.get('feedback_data', {})
            st.session_state.user_stats = data.get('user_stats', st.session_state.user_stats)
            st.sidebar.success("✅ Data loaded successfully!")
        except Exception as e:
            st.sidebar.error("❌ Invalid file format")
    
    # Save data button
    if st.sidebar.button("💾 Save All"):
        save_data = {
            'contacts': st.session_state.contacts,
            'journal_entries': st.session_state.journal_entries,
            'feedback_data': st.session_state.feedback_data,
            'user_stats': st.session_state.user_stats,
            'saved_at': datetime.datetime.now().isoformat()
        }
        filename = f"third_voice_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
        st.sidebar.download_button(
            "📥 Download File",
            json.dumps(save_data, indent=2),
            filename,
            "application/json",
            use_container_width=True
        )


def render_header():
    """Render the main header section."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.svg", width=200)
        except FileNotFoundError:
            st.markdown("# 🎙️ The Third Voice")
        st.markdown(
            "<div style='text-align: center'><i>Created by Predrag Mirković</i></div>",
            unsafe_allow_html=True
        )
    
    st.markdown(f"### 💬 Communicating with: **{st.session_state.active_contact}**")


def render_main_actions():
    """Render the main action buttons."""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Coach My Message", type="primary", use_container_width=True):
            st.session_state.active_mode = "coach"
            st.rerun()
    
    with col2:
        if st.button("📥 Understand Their Message", type="primary", use_container_width=True):
            st.session_state.active_mode = "translate"
            st.rerun()


def process_message(message: str, mode: str):
    """Process a message through AI coaching or translation."""
    contact = st.session_state.contacts[st.session_state.active_contact]
    result = get_ai_response(message, contact['context'], mode == "translate")
    
    if "error" in result:
        st.error(f"❌ {result['error']}")
        return
    
    # Display AI response
    st.markdown("### 🎙️ The Third Voice says:")
    
    if mode == "coach":
        st.markdown(
            f'<div class="ai-response">'
            f'<strong>✨ Your improved message:</strong><br><br>'
            f'{result["improved"]}<br><br>'
            f'<small><i>Generated by: {result["model"]}</i></small>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.session_state.user_stats['coached_messages'] += 1
    else:
        st.markdown(
            f'<div class="ai-response">'
            f'<strong>🔍 What they really mean:</strong><br>'
            f'{result["response"]}<br><br>'
            f'<small><i>Generated by: {result["model"]}</i></small>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.session_state.user_stats['translated_messages'] += 1
    
    # Save to history
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
    
    # Feedback collection
    collect_feedback(history_entry)
    st.success("✅ Saved to history")


def collect_feedback(history_entry: Dict[str, Any]):
    """Collect user feedback on AI responses."""
    st.markdown("### 📊 Was this helpful?")
    col1, col2, col3 = st.columns(3)
    
    feedback_options = [
        ("👍 Yes", "positive", col1),
        ("👌 Okay", "neutral", col2),
        ("👎 No", "negative", col3)
    ]
    
    for label, value, col in feedback_options:
        with col:
            if st.button(label, key=f"{value}_{history_entry['id']}"):
                st.session_state.feedback_data[history_entry['id']] = value
                st.success("Thanks for the feedback!")


def render_message_interface():
    """Render the message input and processing interface."""
    if not st.session_state.active_mode:
        return
    
    mode = st.session_state.active_mode
    
    # Back button
    if st.button("← Back"):
        st.session_state.active_mode = None
        st.rerun()
    
    # Input area
    input_class = "user-msg" if mode == "coach" else "contact-msg"
    prompt_text = "📤 Your message to send:" if mode == "coach" else "📥 Message you received:"
    
    st.markdown(
        f'<div class="{input_class}"><strong>{prompt_text}</strong></div>',
        unsafe_allow_html=True
    )
    
    placeholder = ("Type your message here..." if mode == "coach" 
                  else "Paste their message here...")
    
    message = st.text_area(
        "",
        height=120,
        key=f"{mode}_input",
        label_visibility="collapsed",
        placeholder=placeholder
    )
    
    # Action buttons
    col1, col2 = st.columns([3, 1])
    
    with col1:
        button_text = "🚀 Improve My Message" if mode == "coach" else "🔍 Analyze & Respond"
        process_btn = st.button(button_text, type="secondary")
    
    with col2:
        if st.button("Clear", type="secondary"):
            st.session_state[f"{mode}_input"] = ""
            st.rerun()
    
    # Process message
    if process_btn:
        if message.strip():
            with st.spinner("🎙️ The Third Voice is analyzing..."):
                process_message(message, mode)
        else:
            st.warning("⚠️ Please enter a message first.")


def render_history_tab():
    """Render the history tab."""
    st.markdown(f"### 📜 History with {st.session_state.active_contact}")
    contact = st.session_state.contacts[st.session_state.active_contact]
    
    if not contact['history']:
        st.info(f"No messages yet with {st.session_state.active_contact}. "
               f"Use the buttons above to get started!")
        return
    
    # Filter options
    filter_type = st.selectbox("Filter:", ["All", "Coached Messages", "Understood Messages"])
    
    filtered_history = contact['history']
    if filter_type == "Coached Messages":
        filtered_history = [h for h in contact['history'] if h['type'] == 'coach']
    elif filter_type == "Understood Messages":
        filtered_history = [h for h in contact['history'] if h['type'] == 'translate']
    
    # Display history entries
    for entry in reversed(filtered_history):
        preview = f"{entry['original'][:50]}..." if len(entry['original']) > 50 else entry['original']
        
        with st.expander(f"**{entry['time']}** • {entry['type'].title()} • {preview}"):
            if entry['type'] == 'coach':
                st.markdown(
                    f'<div class="user-msg">📤 <strong>Original:</strong> {entry["original"]}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="ai-response">🎙️ <strong>Improved:</strong> {entry["result"]}<br>'
                    f'<small><i>by {entry.get("model", "Unknown")}</i></small></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="contact-msg">📥 <strong>They said:</strong> {entry["original"]}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="ai-response">🎙️ <strong>Analysis:</strong> {entry["result"]}<br>'
                    f'<small><i>by {entry.get("model", "Unknown")}</i></small></div>',
                    unsafe_allow_html=True
                )
            
            # Show feedback if available
            if entry.get('id') in st.session_state.feedback_data:
                feedback = st.session_state.feedback_data[entry['id']]
                emoji_map = {"positive": "👍", "neutral": "👌", "negative": "👎"}
                st.markdown(f"*Your feedback: {emoji_map.get(feedback, '❓')}*")


def render_journal_tab():
    """Render the journal tab."""
    st.markdown(f"### 📘 Communication Journal - {st.session_state.active_contact}")
    contact_key = st.session_state.active_contact
    
    if contact_key not in st.session_state.journal_entries:
        st.session_state.journal_entries[contact_key] = {
            'what_worked': '',
            'what_didnt': '',
            'insights': '',
            'patterns': ''
        }
    
    journal = st.session_state.journal_entries[contact_key]
    
    col1, col2 = st.columns(2)
    
    journal_sections = [
        ("💚 What worked well?", "what_worked", "Communication strategies that were successful..."),
        ("🔍 Key insights?", "insights", "Important realizations about this relationship..."),
        ("⚠️ What didn't work?", "what_didnt", "What caused issues or misunderstandings..."),
        ("📊 Patterns noticed?", "patterns", "Communication patterns you've observed...")
    ]
    
    for i, (title, key, placeholder) in enumerate(journal_sections):
        col = col1 if i % 2 == 0 else col2
        
        with col:
            st.markdown('<div class="journal-section">', unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            journal[key] = st.text_area(
                "",
                value=journal[key],
                key=f"{key}_{contact_key}",
                height=100,
                placeholder=placeholder
            )
            st.markdown("</div>", unsafe_allow_html=True)


def render_stats_tab():
    """Render the statistics tab."""
    st.markdown("### 📊 Your Communication Stats")
    
    # Main stats
    col1, col2, col3 = st.columns(3)
    stats = st.session_state.user_stats
    
    stat_cards = [
        (stats["total_messages"], "Total Messages", col1),
        (stats["coached_messages"], "Messages Coached", col2),
        (stats["translated_messages"], "Messages Understood", col3)
    ]
    
    for value, label, col in stat_cards:
        with col:
            st.markdown(
                f'<div class="stats-card"><h3>{value}</h3><p>{label}</p></div>',
                unsafe_allow_html=True
            )
    
    # Contact breakdown
    st.markdown("### 👥 By Contact")
    for name, contact in st.session_state.contacts.items():
        if contact['history']:
            coached = sum(1 for h in contact['history'] if h['type'] == 'coach')
            translated = sum(1 for h in contact['history'] if h['type'] == 'translate')
            total = len(contact['history'])
            st.markdown(f"**{name}:** {total} total ({coached} coached, {translated} understood)")
    
    # Feedback summary
    if st.session_state.feedback_data:
        st.markdown("### 📝 Feedback Summary")
        feedback_counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for feedback in st.session_state.feedback_data.values():
            if feedback in feedback_counts:
                feedback_counts[feedback] += 1
        
        st.markdown(
            f"👍 Positive: {feedback_counts['positive']} | "
            f"👌 Neutral: {feedback_counts['neutral']} | "
            f"👎 Negative: {feedback_counts['negative']}"
        )


def render_about_tab():
    """Render the about tab."""
    st.markdown("""
    ### ℹ️ About The Third Voice
    
    **The communication coach that's there when you need it most.**
    
    Instead of repairing relationships after miscommunication damage, 
    The Third Voice helps you communicate better in real-time.
    
    **How it works:**
    1. **Select your contact** - Each relationship gets personalized coaching
    2. **Coach your messages** - Improve what you're about to send
    3. **Understand their messages** - Decode the real meaning behind their words
    4. **Build better patterns** - Journal and learn from each interaction
    
    **Key Features:**
    - 🎯 Context-aware coaching for different relationships
    - 📊 Track your communication progress
    - 📘 Personal journal for insights
    - 💾 Export/import your data
    - 🔒 Privacy-first design
    
    **Privacy First:** All data stays on your device. Save and load your own files.
    
    **Beta v1.0.0** — Built with ❤️ to heal relationships through better communication.
    
    *"When both people are talking from pain, someone needs to be the third voice."*
    
    ---
    
    **Support & Community:**
    - 💬 Join discussions at our community forum
    - 📧 Report bugs or suggest features
    - 🌟 Share your success stories
    
    **Technical Details:**
    - Powered by OpenRouter API
    - Uses multiple AI models for reliability
    - Built with Streamlit for easy deployment
    """)


def main():
    """Main application function."""
    setup_page()
    initialize_session_state()
    
    # Token validation
    if not validate_token():
        st.stop()
    
    # Render main interface
    render_sidebar()
    render_header()
    render_main_actions()
    render_message_interface()
    
    # Render tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📜 History", "📘 Journal", "📊 Stats", "ℹ️ About"])
    
    with tab1:
        render_history_tab()
    
    with tab2:
        render_journal_tab()
    
    with tab3:
        render_stats_tab()
    
    with tab4:
        render_about_tab()


if __name__ == "__main__":
    main()
