"""
The Third Voice AI - Main Application
A revolutionary communication assistance platform built with love for families

Created by Predrag Mirković from detention, fighting to come home to Samantha 💖
"When both people are talking from pain, someone needs to be the third voice."
"""

import streamlit as st
import json
import datetime
from typing import Optional

# Add to your existing imports
from modules.config import apply_styles, toggle_theme

# Voice Command Detector (Add to your main message processing loop)
if 'user_input' in st.session_state:
    user_msg = st.session_state.user_input.lower()
    
    # Theme commands
    if any(phrase in user_msg for phrase in ["dark theme", "dark mode"]):
        toggle_theme('dark')
        st.rerun()  # Refresh to apply changes
        
    elif any(phrase in user_msg for phrase in ["light theme", "light mode"]):
        toggle_theme('light')
        st.rerun()

# Import our modular components
from modules.config import apply_styles, REQUIRE_TOKEN, VALID_TOKENS, CONTEXTS
from modules.session_state import (
    initialize_session_state, 
    get_current_contact,
    add_contact,
    delete_contact,
    add_history_entry,
    update_user_stats,
    set_feedback,
    get_contact_stats,
    get_feedback_stats,
    export_session_data,
    import_session_data
)
from modules.utils import (
    get_ai_response,
    create_history_entry,
    validate_token,
    generate_filename,
    truncate_text,
    sanitize_input,
    health_check
)

# Configure the page
st.set_page_config(
    page_title="The Third Voice AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def authenticate_user():
    """Handle user authentication for beta access"""
    if REQUIRE_TOKEN and not st.session_state.get('token_validated', False):
        st.markdown("# 🎙️ The Third Voice")
        st.markdown("*Your AI Communication Coach*")
        st.warning("🔐 Access restricted. Enter beta token to continue.")
        
        token = st.text_input("Beta Token:", type="password")
        
        if st.button("Validate Access"):
            if validate_token(token):
                st.session_state.token_validated = True
                st.success("✅ Welcome to The Third Voice beta!")
                st.rerun()
            else:
                st.error("❌ Invalid token. Contact support for access.")
        
        st.stop()

def render_header():
    """Render the main header with logo and branding"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Try to load logo, fallback to text
        try:
            st.image("logo.svg", width=200)
        except:
            st.markdown("# 🎙️ The Third Voice")
        
        st.markdown(
            "<div style='text-align: center'>"
            "<i>Created by Predrag Mirković</i><br>"
            "<small>Building bridges through better communication</small>"
            "</div>", 
            unsafe_allow_html=True
        )

def render_sidebar():
    """Render the sidebar with contact management and data controls"""
    st.sidebar.markdown("### 👥 Your Contacts")
    
    # Add new contact
    with st.sidebar.expander("➕ Add Contact"):
        new_name = st.text_input("Contact Name:", key="new_contact_name")
        new_context = st.selectbox("Relationship Type:", CONTEXTS, key="new_contact_context")
        
        if st.button("Add Contact", key="add_contact_btn"):
            if new_name and new_name.strip():
                clean_name = sanitize_input(new_name.strip())
                if add_contact(clean_name, new_context):
                    st.success(f"✅ Added {clean_name}")
                    st.rerun()
                else:
                    st.error("Contact already exists!")
            else:
                st.error("Please enter a contact name.")
    
    # Contact selection
    contact_names = list(st.session_state.contacts.keys())
    if contact_names:
        selected = st.sidebar.radio(
            "Active Contact:", 
            contact_names, 
            index=contact_names.index(st.session_state.active_contact)
        )
        st.session_state.active_contact = selected
    
    # Contact info
    current_contact = get_current_contact()
    contact_stats = get_contact_stats(st.session_state.active_contact)
    
    st.sidebar.markdown(
        f"**Context:** {current_contact['context']}\n"
        f"**Total Messages:** {contact_stats['total']}\n"
        f"**Coached:** {contact_stats['coached']}\n"
        f"**Translated:** {contact_stats['translated']}"
    )
    
    # Delete contact (except General)
    if st.session_state.active_contact != "General":
        if st.sidebar.button("🗑️ Delete Contact", key="delete_contact"):
            if delete_contact(st.session_state.active_contact):
                st.success("Contact deleted")
                st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Data Management")
    
    # Data import
    uploaded_file = st.sidebar.file_uploader(
        "📤 Import Data", 
        type="json", 
        key="data_import"
    )
    
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            if import_session_data(data):
                st.sidebar.success("✅ Data imported successfully!")
                st.rerun()
            else:
                st.sidebar.error("❌ Import failed - invalid data")
        except Exception as e:
            st.sidebar.error(f"❌ Import error: {str(e)}")
    
    # Data export
    if st.sidebar.button("💾 Export Data", key="data_export"):
        export_data = export_session_data()
        filename = generate_filename()
        st.sidebar.download_button(
            "📥 Download Data",
            data=json.dumps(export_data, indent=2),
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )

def render_main_interface():
    """Render the main communication interface"""
    st.markdown(f"### 💬 Communicating with: **{st.session_state.active_contact}**")
    
    # Mode selection buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "📤 Coach My Message", 
            type="primary", 
            use_container_width=True,
            key="coach_mode_btn"
        ):
            st.session_state.active_mode = "coach"
            st.rerun()
    
    with col2:
        if st.button(
            "📥 Understand Their Message", 
            type="primary", 
            use_container_width=True,
            key="translate_mode_btn"
        ):
            st.session_state.active_mode = "translate"
            st.rerun()

def render_message_processor():
    """Handle message input and AI processing"""
    if not st.session_state.get('active_mode'):
        return
    
    mode = st.session_state.active_mode
    
    # Back button
    if st.button("← Back", key="back_btn"):
        st.session_state.active_mode = None
        st.rerun()
    
    # Mode-specific UI
    input_class = "user-msg" if mode == "coach" else "contact-msg"
    title_text = "📤 Your message to send:" if mode == "coach" else "📥 Message you received:"
    placeholder = "Type your message here..." if mode == "coach" else "Paste their message here..."
    
    st.markdown(
        f'<div class="{input_class}"><strong>{title_text}</strong></div>', 
        unsafe_allow_html=True
    )
    
    # Message input
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
        process_btn_text = "🚀 Improve My Message" if mode == "coach" else "🔍 Analyze & Respond"
        process_btn = st.button(process_btn_text, type="primary", key="process_btn")
    
    with col2:
        if st.button("Clear", type="secondary", key="clear_btn"):
            st.session_state[f"{mode}_input"] = ""
            st.rerun()
    
    # Process message
    if process_btn and message.strip():
        clean_message = sanitize_input(message.strip())
        
        with st.spinner("🎙️ The Third Voice is analyzing..."):
            current_contact = get_current_contact()
            result = get_ai_response(clean_message, current_contact['context'], mode == "translate")
            
            if "error" not in result:
                render_ai_response(result, mode)
                
                # Create and save history entry
                history_entry = create_history_entry(clean_message, result, mode)
                add_history_entry(st.session_state.active_contact, history_entry)
                update_user_stats(mode)
                
                # Feedback section
                render_feedback_section(history_entry)
                
                st.success("✅ Saved to history")
            else:
                st.error(f"❌ {result['error']}")
    
    elif process_btn:
        st.warning("⚠️ Please enter a message first.")

def render_ai_response(result: dict, mode: str):
    """Display AI response in formatted manner"""
    st.markdown("### 🎙️ The Third Voice says:")
    
    if mode == "coach":
        st.markdown(
            f'<div class="ai-response">'
            f'<strong>✨ Your improved message:</strong><br><br>'
            f'{result.get("improved", "")}<br><br>'
            f'<small><i>Generated by: {result.get("model", "Unknown")}</i></small>'
            f'</div>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="ai-response">'
            f'<strong>🔍 What they really mean:</strong><br>'
            f'{result.get("response", "")}<br><br>'
            f'<small><i>Generated by: {result.get("model", "Unknown")}</i></small>'
            f'</div>', 
            unsafe_allow_html=True
        )

def render_feedback_section(history_entry: dict):
    """Render feedback collection interface"""
    st.markdown("### 📊 Was this helpful?")
    
    col1, col2, col3 = st.columns(3)
    feedback_options = [
        ("👍 Yes", "positive"),
        ("👌 Okay", "neutral"),
        ("👎 No", "negative")
    ]
    
    for idx, (label, sentiment) in enumerate(feedback_options):
        with [col1, col2, col3][idx]:
            if st.button(label, key=f"feedback_{sentiment}_{history_entry['id']}"):
                set_feedback(history_entry['id'], sentiment)
                st.success("Thanks for the feedback!")

def render_history_tab():
    """Render the conversation history tab"""
    st.markdown(f"### 📜 History with {st.session_state.active_contact}")
    
    current_contact = get_current_contact()
    history = current_contact.get('history', [])
    
    if not history:
        st.info(f"No messages yet with {st.session_state.active_contact}. Use the buttons above to get started!")
        return
    
    # Filter options
    filter_type = st.selectbox("Filter:", ["All", "Coached Messages", "Understood Messages"])
    
    filtered_history = history
    if filter_type == "Coached Messages":
        filtered_history = [h for h in history if h['type'] == 'coach']
    elif filter_type == "Understood Messages":
        filtered_history = [h for h in history if h['type'] == 'translate']
    
    # Display history entries
    for entry in reversed(filtered_history):
        preview_text = truncate_text(entry.get('original', ''), 50)
        
        with st.expander(f"**{entry['time']}** • {entry['type'].title()} • {preview_text}..."):
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
            
            # Show existing feedback
            feedback = st.session_state.feedback_data.get(entry.get('id'))
            if feedback:
                emoji_map = {"positive": "👍", "neutral": "👌", "negative": "👎"}
                st.markdown(f"*Your feedback: {emoji_map.get(feedback, '❓')}*")

def render_journal_tab():
    """Render the communication journal tab"""
    st.markdown(f"### 📘 Communication Journal - {st.session_state.active_contact}")
    
    contact_key = st.session_state.active_contact
    
    # Initialize journal entries for this contact if not exists
    if contact_key not in st.session_state.journal_entries:
        st.session_state.journal_entries[contact_key] = {
            'what_worked': '',
            'what_didnt': '',
            'insights': '',
            'patterns': ''
        }
    
    journal = st.session_state.journal_entries[contact_key]
    
    # Two-column layout for journal entries
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            '<div class="journal-section">**💚 What worked well?**</div>', 
            unsafe_allow_html=True
        )
        journal['what_worked'] = st.text_area(
            "",
            value=journal['what_worked'],
            key=f"worked_{contact_key}",
            height=100,
            placeholder="Communication strategies that were successful..."
        )
        
        st.markdown(
            '<div class="journal-section">**🔍 Key insights?**</div>', 
            unsafe_allow_html=True
        )
        journal['insights'] = st.text_area(
            "",
            value=journal['insights'],
            key=f"insights_{contact_key}",
            height=100,
            placeholder="Important realizations about this relationship..."
        )
    
    with col2:
        st.markdown(
            '<div class="journal-section">**⚠️ What didn\'t work?**</div>', 
            unsafe_allow_html=True
        )
        journal['what_didnt'] = st.text_area(
            "",
            value=journal['what_didnt'],
            key=f"didnt_{contact_key}",
            height=100,
            placeholder="What caused issues or misunderstandings..."
        )
        
        st.markdown(
            '<div class="journal-section">**📊 Patterns noticed?**</div>', 
            unsafe_allow_html=True
        )
        journal['patterns'] = st.text_area(
            "",
            value=journal['patterns'],
            key=f"patterns_{contact_key}",
            height=100,
            placeholder="Communication patterns you've observed..."
        )

def render_stats_tab():
    """Render the statistics and analytics tab"""
    st.markdown("### 📊 Your Communication Stats")
    
    # Overall stats
    stats = st.session_state.user_stats
    col1, col2, col3 = st.columns(3)
    
    stat_items = [
        (stats.get("total_messages", 0), "Total Messages"),
        (stats.get("coached_messages", 0), "Messages Coached"),
        (stats.get("translated_messages", 0), "Messages Understood")
    ]
    
    for idx, (stat, label) in enumerate(stat_items):
        with [col1, col2, col3][idx]:
            st.markdown(
                f'<div class="stats-card"><h3>{stat}</h3><p>{label}</p></div>', 
                unsafe_allow_html=True
            )
    
    # Stats by contact
    st.markdown("### 👥 By Contact")
    for name, contact in st.session_state.contacts.items():
        contact_stats = get_contact_stats(name)
        if contact_stats['total'] > 0:
            st.markdown(
                f"**{name}:** {contact_stats['total']} total "
                f"({contact_stats['coached']} coached, {contact_stats['translated']} understood)"
            )
    
    # Feedback summary
    feedback_stats = get_feedback_stats()
    if any(feedback_stats.values()):
        st.markdown("### 📝 Feedback Summary")
        st.markdown(
            f"👍 Positive: {feedback_stats['positive']} | "
            f"👌 Neutral: {feedback_stats['neutral']} | "
            f"👎 Negative: {feedback_stats['negative']}"
        )

def render_about_tab():
    """Render the about/help tab"""
    st.markdown("""
    ### ℹ️ About The Third Voice
    
    **The communication coach that's there when you need it most.**
    
    Instead of repairing relationships after miscommunication damage, The Third Voice helps you communicate better in real-time.
    
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
    - Open source and community-driven
    """)

def render_tabs():
    """Render all application tabs"""
    tab1, tab2, tab3, tab4 = st.tabs(["📜 History", "📘 Journal", "📊 Stats", "ℹ️ About"])
    
    with tab1:
        render_history_tab()
    
    with tab2:
        render_journal_tab()
    
    with tab3:
        render_stats_tab()
    
    with tab4:
        render_about_tab()

def main():
    """Main application entry point"""
    # Apply styling
    apply_styles()
    
    # Initialize session state
    initialize_session_state()
    
    # Authenticate user
    authenticate_user()
    
    # Render main interface
    render_header()
    render_sidebar()
    render_main_interface()
    render_message_processor()
    render_tabs()
    
    # Health check in development
    if st.secrets.get("DEBUG", False):
        with st.expander("🔧 Debug Info"):
            st.json({
                "session_state_keys": list(st.session_state.keys()),
                "active_contact": st.session_state.get('active_contact'),
                "active_mode": st.session_state.get('active_mode'),
                "health_check": health_check()
            })

if __name__ == "__main__":
    main()
