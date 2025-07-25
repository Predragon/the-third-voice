"""
app.py - The Third Voice AI Main Engine

The orchestrator of our mission: clean, focused, and mobile-friendly.
Built by a father in detention, for every family seeking healing.

"When both people are speaking from pain, someone must be the third voice."
"""

import streamlit as st
import json
from datetime import datetime

# Import our modularized components
from ai_core import (
    interpret_message, process_ai_transformation, 
    calculate_relationship_health_score, get_healing_insights,
    create_message_hash, get_ai_cache_key, PRIMARY_MODEL,
    get_model_status_info
)
from data_backend import (
    get_current_user_id, restore_user_session,
    sign_up, sign_in, sign_out, resend_verification_email,
    load_contacts_and_history, save_contact, delete_contact,
    save_message, save_interpretation, get_cached_response, 
    cache_ai_response, save_feedback, test_database_connection,
    get_user_stats
)

# Model consistency fix
MODEL = PRIMARY_MODEL

# === CONSTANTS ===
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}


# === PAGE CONFIGURATION ===
def configure_page():
    """Configure Streamlit page settings and mobile optimization"""
    st.set_page_config(
        page_title="The Third Voice AI - Family Healing Through Better Communication",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",  # Fixed: Changed from "collapsed" to "expanded"
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "The Third Voice AI - When both people are speaking from pain, someone must be the third voice."
        }
    )
    
    # Mobile-optimized CSS with proper colors
    st.markdown("""
    <style>
        /* Hide Streamlit branding and optimize for mobile */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container styling */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        
        /* Button styling for better mobile interaction */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            border: none;
            padding: 0.75rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
            background-color: #4CAF50;
            color: white;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: #45a049;
        }
        
        /* Primary action buttons */
        .stButton > button[kind="primary"] {
            background-color: #2196F3;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #1976D2;
        }
        
        /* Text area improvements */
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            font-size: 16px;
            background-color: white;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }
        
        /* Form styling */
        .stForm {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            background: #fafafa;
            margin: 1rem 0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            border-radius: 8px;
            background-color: #f0f2f6;
            border: 1px solid #e0e0e0;
        }
        
        /* Metric styling */
        [data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Success/error message styling */
        .stSuccess {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .stError {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .stWarning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .stInfo {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Input field styling */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            background-color: white;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }
        
        /* Select box styling */
        .stSelectbox > div > div > select {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            background-color: white;
        }
        
        /* Mobile-specific adjustments */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            h1, h2, h3 {
                font-size: 1.2em !important;
                line-height: 1.3;
            }
            
            .stButton > button {
                padding: 0.6rem 0.8rem;
                font-size: 14px;
            }
        }
        
        /* Ensure proper background colors */
        .main {
            background-color: white;
        }
        
        /* Card-like containers */
        .element-container {
            background-color: white;
        }
    </style>
    """, unsafe_allow_html=True)


# === SESSION STATE INITIALIZATION ===
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'authenticated': False,
        'user': None,
        'app_mode': "login",
        'contacts': {},
        'active_contact': None,
        'edit_contact': None,
        'conversation_input_text': "",
        'clear_conversation_input': False,
        'edit_contact_name_input': "",
        'add_contact_name_input': "",
        'add_contact_context_select': list(CONTEXTS.keys())[0],
        'last_error_message': None,
        'show_verification_notice': False,
        'verification_email': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# === SIDEBAR WITH USER INFO AND DEBUG ===
def render_sidebar():
    """Render sidebar with user info and debug information"""
    if not st.session_state.get("authenticated", False):
        return
    
    with st.sidebar:
        st.markdown("### 👤 User Info")
        
        user_email = st.session_state.user.email if st.session_state.user else "Unknown"
        st.markdown(f"**Email:** {user_email}")
        
        # User stats
        try:
            stats = get_user_stats()
            if stats:
                st.markdown(f"**Contacts:** {stats.get('contact_count', 0)}")
                st.markdown(f"**Messages:** {stats.get('message_count', 0)}")
                if stats.get('last_activity'):
                    last_activity = datetime.fromisoformat(stats['last_activity'].replace('Z', '+00:00'))
                    st.markdown(f"**Last Active:** {last_activity.strftime('%m/%d %H:%M')}")
        except Exception as e:
            st.markdown("*Stats loading...*")
        
        st.markdown("---")
        
        # Sign out button
        if st.button("🚪 Sign Out", use_container_width=True):
            if sign_out():
                st.rerun()
        
        st.markdown("---")
        
        # Debug section
        with st.expander("🔧 Debug Info", expanded=False):
            st.markdown(f"**App Mode:** {st.session_state.get('app_mode', 'Unknown')}")
            st.markdown(f"**Active Contact:** {st.session_state.get('active_contact', 'None')}")
            st.markdown(f"**Total Contacts:** {len(st.session_state.get('contacts', {}))}")
            
            # Database connection test
            db_status = test_database_connection()
            st.markdown(f"**Database:** {db_status}")
            
            # Model status
            try:
                model_info = get_model_status_info()
                st.markdown(f"**AI Model:** {model_info}")
            except:
                st.markdown(f"**AI Model:** {MODEL}")
        
        st.markdown("---")
        st.markdown("### 💙 Mission")
        st.markdown("*Building healing conversations, one family at a time.*")
        
        st.markdown("**Built with love by a father fighting to return to his daughter.**")


# === FEEDBACK SYSTEM UI ===
def show_feedback_widget(context="general"):
    """Display feedback widget"""
    with st.expander("💬 Help us improve The Third Voice", expanded=False):
        st.markdown("*Your feedback helps us build better family healing tools*")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            rating = st.selectbox(
                "How helpful was this?",
                options=[5, 4, 3, 2, 1],
                format_func=lambda x: f"{'⭐' * x} ({x}/5)",
                key=f"feedback_rating_{context}"
            )
        
        with col2:
            feedback_text = st.text_area(
                "What can we improve?",
                placeholder="Share your thoughts, suggestions, or issues...",
                height=80,
                key=f"feedback_text_{context}"
            )
        
        if st.button("Send Feedback", key=f"send_feedback_{context}"):
            if save_feedback(rating, feedback_text, context):
                st.success("Thank you! Your feedback helps us heal more families. 💙")
                # Clear the form
                st.session_state[f"feedback_text_{context}"] = ""
            else:
                st.error("Could not save feedback. Please try again.")


# === CORE MESSAGE PROCESSING ===
def process_message(contact_name, message, context):
    """Enhanced message processing with relationship memory"""
    st.session_state.last_error_message = None
    
    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty. Please type something to transform."
        return
    
    # Get contact info
    contact_data = st.session_state.contacts.get(contact_name)
    if not contact_data:
        st.session_state.last_error_message = "Contact not found."
        return
    
    contact_id = contact_data["id"]
    history = contact_data.get("history", [])
    
    # Check cache first
    message_hash = create_message_hash(message, context)
    cached = get_cached_response(contact_id, message_hash)
    
    if cached:
        # Use cached response
        ai_response_text = cached["response"]
        healing_score = cached["healing_score"]
        ai_sentiment = cached["sentiment"]
        ai_emotional_state = cached["emotional_state"]
        st.info("Using cached response for faster processing")
    else:
        # Generate new response
        with st.spinner("🤖 Processing with relationship insights..."):
            result = process_ai_transformation(contact_name, message, context, history)
            
            if not result.get("success"):
                st.session_state.last_error_message = result.get("error", "Unknown AI processing error")
                return
            
            ai_response_text = result["response"]
            healing_score = result["healing_score"]
            ai_sentiment = result["sentiment"]
            ai_emotional_state = result["emotional_state"]
            
            # Cache the response
            cache_ai_response(contact_id, message_hash, context, ai_response_text, 
                            healing_score, MODEL, ai_sentiment, ai_emotional_state)
    
    # Save the incoming message
    save_message(contact_id, contact_name, "incoming", message, None, "unknown", 0, "N/A")
    
    # Save the AI response
    mode = "translate" if any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"]) else "coach"
    save_message(contact_id, contact_name, mode, message, ai_response_text, ai_emotional_state, healing_score, MODEL, ai_sentiment)
    
    # Store response for immediate display
    st.session_state[f"last_response_{contact_name}"] = {
        "response": ai_response_text,
        "healing_score": healing_score,
        "timestamp": datetime.now().timestamp(),
        "model": MODEL
    }
    
    st.session_state.clear_conversation_input = True
    st.rerun()


# === INTERPRETATION UI COMPONENTS ===
def render_interpret_section(contact_name, message, context, history):
    """Render the interpretation UI section"""
    if st.button("🔍 Interpret - What do they really mean?", key="interpret_btn", help="Reveal emotional subtext and healing opportunities"):
        with st.spinner("🧠 Analyzing emotional subtext..."):
            result = interpret_message(contact_name, message, context, history)
            
            if result.get("success"):
                st.session_state[f"last_interpretation_{contact_name}"] = {
                    "interpretation": result["interpretation"],
                    "score": result["interpretation_score"],
                    "timestamp": datetime.now().timestamp(),
                    "original_message": message
                }
                
                # Save to database
                contact_data = st.session_state.contacts.get(contact_name, {})
                contact_id = contact_data.get("id")
                if contact_id:
                    save_interpretation(contact_id, contact_name, message, result["interpretation"], result["interpretation_score"], result["model"])
                
                st.rerun()
            else:
                st.error(f"Could not analyze message: {result.get('error', 'Unknown error')}")


def display_interpretation_result(contact_name):
    """Display interpretation results if available"""
    interp_key = f"last_interpretation_{contact_name}"
    if interp_key in st.session_state:
        interp_data = st.session_state[interp_key]
        
        # Show if recent (within 10 minutes)
        if datetime.now().timestamp() - interp_data["timestamp"] < 600:
            with st.expander("🔍 **Emotional Analysis - What They Really Mean**", expanded=True):
                st.markdown(interp_data["interpretation"])
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    score = interp_data["score"]
                    if score >= 8:
                        st.success(f"✨ Deep Insight Score: {score}/10 - Very revealing analysis")
                    elif score >= 6:
                        st.info(f"💡 Insight Score: {score}/10 - Good understanding")
                    else:
                        st.warning(f"🔍 Insight Score: {score}/10 - Basic analysis")
                
                with col2:
                    if st.button("📋 Copy", key="copy_interpretation"):
                        st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
        else:
            # Clear old interpretation
            del st.session_state[interp_key]


def display_relationship_progress(contact_name, history):
    """Display relationship healing progress and insights"""
    if not history:
        return
    
    with st.expander("📊 **Relationship Healing Progress**", expanded=False):
        health_score, status = calculate_relationship_health_score(history)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Relationship Health", f"{health_score}/10", help="Based on recent healing scores")
        with col2:
            st.metric("Total Conversations", len(history))
        
        st.markdown(f"**Status:** {status}")
        
        # Healing insights
        insights = get_healing_insights(history)
        st.markdown("**💙 Your Healing Journey:**")
        for insight in insights:
            st.markdown(f"• {insight}")
        
        # Recent trend visualization (simple text-based for now)
        if len(history) >= 5:
            recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
            if recent_scores:
                trend_text = " → ".join([str(score) for score in recent_scores])
                st.markdown(f"**Recent Healing Scores:** {trend_text}")


# === ADD CONTACT VIEW ===
def render_add_contact_view():
    st.markdown("### ➕ Add New Contact")
    
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        st.session_state.app_mode = "contacts_list"
        st.session_state.last_error_message = None
        st.rerun()
    
    st.markdown("**Tell us about this relationship so we can provide better guidance:**")
    
    with st.form("add_contact_form"):
        name = st.text_input("Contact Name", placeholder="Sarah, Mom, Dad, Boss...", key="add_contact_name_input_widget")
        context = st.selectbox(
            "Relationship Type", 
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()} - {CONTEXTS[x]['description']}",
            key="add_contact_context_select_widget"
        )
        
        if st.form_submit_button("Add Contact", use_container_width=True):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.contacts = load_contacts_and_history()
                    st.success(f"Added {name.strip()}! Ready to start healing conversations.")
                    st.session_state.app_mode = "contacts_list"
                    st.rerun()
            else:
                st.error("Contact name cannot be empty.")


def render_edit_contact_view():
    if not st.session_state.edit_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    
    contact = st.session_state.edit_contact
    st.markdown(f"### ✏️ Edit Contact: {contact['name']}")
    
    if st.button("← Back", key="back_to_conversation", use_container_width=True):
        st.session_state.app_mode = "conversation_view"
        st.session_state.edit_contact = None
        st.rerun()
    
    with st.form("edit_contact_form"):
        name_input = st.text_input("Name", value=contact["name"], key="edit_contact_name_input_widget")
        
        context_options = list(CONTEXTS.keys())
        initial_context_index = context_options.index(contact["context"]) if contact["context"] in context_options else 0
        context = st.selectbox(
            "Relationship", 
            context_options,
            index=initial_context_index,
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
            key="edit_contact_context_select"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                new_name = name_input.strip()
                if not new_name:
                    st.error("Contact name cannot be empty.")
                elif save_contact(new_name, context, contact["id"]):
                    if st.session_state.active_contact == contact["name"]:
                        st.session_state.active_contact = new_name
                    st.success(f"Updated {new_name}")
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.app_mode = "conversation_view"
                    st.session_state.edit_contact = None
                    st.rerun()
        
        with col2:
            if st.form_submit_button("🗑️ Delete Contact"):
                if delete_contact(contact["id"]):
                    st.success(f"Deleted contact: {contact['name']}")
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.app_mode = "contacts_list"
                    st.session_state.active_contact = None
                    st.session_state.edit_contact = None
                    st.rerun()


def render_conversation_view():
    """The heart of our app - where healing happens"""
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    
    # Navigation buttons
    back_col, edit_col, _ = st.columns([2, 2, 6])
    with back_col:
        if st.button("← Back", key="back_btn", use_container_width=True):
            st.session_state.app_mode = "contacts_list"
            st.session_state.active_contact = None
            st.session_state.last_error_message = None
            st.session_state.clear_conversation_input = False
            st.rerun()
    
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            st.session_state.app_mode = "edit_contact_view"
            st.rerun()
    
    # Relationship progress section
    display_relationship_progress(contact_name, history)
    
    st.markdown("---")
    
    # Input section
    st.markdown("#### 💭 Your Input")
    st.markdown("*Share what happened - their message or your response that needs guidance*")
    
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    st.text_area(
        "What's happening?",
        value=input_value,
        key="conversation_input_text",
        placeholder="Examples:\n• They said: 'You never listen to me!'\n• I want to tell them: 'I'm frustrated with your attitude'\n• We had a fight about...",
        height=120
    )
    
    if st.session_state.clear_conversation_input:
        st.session_state.clear_conversation_input = False
    
    # Action buttons
    current_message = st.session_state.conversation_input_text
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message", use_container_width=True):
            process_message(contact_name, current_message, context)
    
    with col2:
        # Interpret button
        if current_message.strip():
            render_interpret_section(contact_name, current_message, context, history)
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first", use_container_width=True)
    
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    
    # Error display
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    
    # Show interpretation results if available
    display_interpretation_result(contact_name)
    
    st.markdown("---")
    
    # AI Response section
    st.markdown("#### 🤖 The Third Voice Guidance")
    last_response_key = f"last_response_{contact_name}"
    
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        
        # Show response if it's recent (within 5 minutes)
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            with st.container():
                st.markdown("**Your AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                
                col_score, col_model, col_copy = st.columns([2, 2, 1])
                with col_score:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Healing Score: {last_resp['healing_score']}/10 - Transformative guidance")
                    elif last_resp["healing_score"] >= 6:
                        st.info(f"💙 Healing Score: {last_resp['healing_score']}/10 - Good guidance")
                    else:
                        st.warning(f"⚠️ Healing Score: {last_resp['healing_score']}/10 - Basic guidance")
                
                with col_model:
                    st.caption(f"Model: {last_resp['model']}")
                
                with col_copy:
                    if st.button("📋 Copy", key="copy_response"):
                        st.info("Click inside the text area above, Ctrl+A to select all, then Ctrl+C to copy")
        else:
            # Clear old response
            del st.session_state[last_response_key]
    else:
        st.info("💡 Enter a message above and click **Transform with Love** to get AI guidance for healing communication.")
    
    st.markdown("---")
    
    # Conversation history section
    if history:
        st.markdown("#### 📚 Recent Conversations")
        with st.expander(f"View {len(history)} conversation{'s' if len(history) != 1 else ''}", expanded=False):
            # Show last 10 conversations in reverse chronological order
            recent_history = history[-10:][::-1]
            
            for i, msg in enumerate(recent_history):
                col_time, col_score = st.columns([3, 1])
                
                with col_time:
                    st.markdown(f"**{msg['time']}** - {msg['type'].title()}")
                
                with col_score:
                    if msg.get('healing_score', 0) > 0:
                        score_color = "🟢" if msg['healing_score'] >= 7 else "🟡" if msg['healing_score'] >= 5 else "🔴"
                        st.markdown(f"{score_color} {msg['healing_score']}/10")
                
                st.markdown(f"**Input:** {msg['original'][:100]}{'...' if len(msg['original']) > 100 else ''}")
                
                if msg.get('result'):
                    st.markdown(f"**Response:** {msg['result'][:150]}{'...' if len(msg['result']) > 150 else ''}")
                
                if i < len(recent_history) - 1:
                    st.markdown("---")
    
    # Add conversation-specific feedback
    show_feedback_widget(f"conversation_{contact_name}")


# === MAIN APPLICATION ROUTER ===
def main_app():
    """Main application routing and logic"""
    
    # Try to restore session first
    if not st.session_state.get("authenticated", False):
        restore_user_session()
    
    # Handle verification notice display
    if st.session_state.get("show_verification_notice", False):
        verification_notice_page()
        return
    
    # Authentication check
    if not st.session_state.get("authenticated", False):
        if st.session_state.app_mode == "signup":
            signup_page()
        else:
            login_page()
        return
    
    # Main authenticated app routing
    app_mode = st.session_state.get("app_mode", "contacts_list")
    
    if app_mode == "first_time_setup":
        render_first_time_screen()
    elif app_mode == "contacts_list":
        render_contacts_list_view()
    elif app_mode == "add_contact_view":
        render_add_contact_view()
    elif app_mode == "edit_contact_view":
        render_edit_contact_view()
    elif app_mode == "conversation_view":
        render_conversation_view()
    else:
        # Fallback to contacts list for unknown modes
        st.session_state.app_mode = "contacts_list"
        st.rerun()


# === UI PAGES ===
def verification_notice_page():
    """Complete email verification notice page"""
    st.title("🎙️ Welcome to The Third Voice AI")
    
    st.success("✅ Account created successfully!")
    
    st.markdown("### 📧 Check Your Email")
    st.info(f"""
    **Verification email sent to:** `{st.session_state.verification_email}`
    
    **Next steps:**
    1. Check your email inbox (and spam folder)
    2. Click the verification link in the email
    3. Return here and log in
    
    **⏰ The verification email may take a few minutes to arrive.**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📨 Resend Verification Email", use_container_width=True):
            if resend_verification_email(st.session_state.verification_email):
                st.success("Verification email resent!")
    
    with col2:
        if st.button("🔑 Go to Login", use_container_width=True):
            st.session_state.app_mode = "login"
            st.session_state.show_verification_notice = False
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 💙 Welcome to The Family Healing Revolution")
    st.markdown("""
    **The Third Voice AI** helps families communicate with love, understanding, and healing. 
    You're about to join thousands of people rebuilding their most important relationships.
    
    *"When both people are speaking from pain, someone must be the third voice."*
    """)
    
    # Add helpful tips while they wait
    with st.expander("💡 What to expect after verification", expanded=True):
        st.markdown("""
        **Once you're verified and logged in, you'll be able to:**
        
        - ✨ Transform difficult conversations into healing moments
        - 💕 Get guidance for romantic, family, work, and friendship relationships  
        - 🎯 Receive personalized coaching based on your relationship context
        - 📊 Track your healing progress with our scoring system
        - 💬 Access your conversation history across all your contacts
        
        **Built by a father separated from his daughter, for every family seeking healing.**
        """)


def login_page():
    st.title("🎙️ The Third Voice AI")
    st.subheader("Login to continue your healing journey.")
    
    # Mission statement at top
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **We are that voice** — calm, wise, and healing.
    """)
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            if sign_in(email, password):
                st.session_state.contacts = load_contacts_and_history()
                if not st.session_state.contacts:
                    st.session_state.app_mode = "first_time_setup"
                else:
                    st.session_state.app_mode = "contacts_list"
                st.success(f"Welcome back, {st.session_state.user.email}!")
                st.rerun()
    
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account", use_container_width=True):
        st.session_state.app_mode = "signup"
        st.rerun()
    
    # Show mission context
    with st.expander("💙 Our Mission", expanded=False):
        st.markdown("""
        **The Third Voice AI** was born from communication breakdowns that shattered a family. 
        We're turning pain into purpose, helping families heal through better conversations.
        
        Built with love by Predrag Mirkovic, fighting to return to his 6-year-old daughter Samantha 
        after 15 months apart. Every feature serves family healing.
        """)


def signup_page():
    st.title("🎙️ Join The Third Voice AI")
    st.subheader("Start your journey towards healthier conversations.")
    
    # Mission context
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **Join thousands rebuilding their most important relationships.**
    """)
    
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password (minimum 6 characters)", type="password", key="signup_password")
        signup_button = st.form_submit_button("Create Account", use_container_width=True)
        
        if signup_button:
            if len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                sign_up(email, password)
    
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login", use_container_width=True):
        st.session_state.app_mode = "login"
        st.rerun()
    
    # Preview what they'll get
    with st.expander("✨ What you'll get access to", expanded=True):
        st.markdown("""
        **🌟 Transform difficult conversations** - Turn anger into understanding
        
        **💕 Multi-relationship support** - Romantic, family, workplace, co-parenting, friendships
        
        **🎯 Context-aware guidance** - AI understands your specific relationship dynamics
        
        **📊 Healing progress tracking** - See your communication improvement over time
        
        **💾 Conversation history** - Access all your guided conversations anytime
        
        **🚀 Always improving** - Built by a father fighting to heal his own family
        """)


def render_first_time_screen():
    st.markdown("### 🎙️ Welcome to The Third Voice")
    st.markdown("**Choose a relationship type to get started, or add a custom contact:**")
    
    cols = st.columns(2)
    contexts_items = list(CONTEXTS.items())
    
    for i, (context_key, context_info) in enumerate(contexts_items):
        with cols[i % 2]:
            if st.button(
                f"{context_info['icon']} {context_key.title()}\n{context_info['description']}",
                key=f"context_{context_key}",
                use_container_width=True
            ):
                default_names = {
                    "romantic": "Partner",
                    "coparenting": "Co-parent", 
                    "workplace": "Colleague",
                    "family": "Family Member",
                    "friend": "Friend"
                }
                contact_name = default_names.get(context_key, context_key.title())
                
                if save_contact(contact_name, context_key):
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.active_contact = contact_name
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()
    
    st.markdown("---")
    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name_input")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="first_time_new_contact_context_select")
        
        if st.form_submit_button("Add Custom Contact", use_container_width=True):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.active_contact = name.strip()
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()
            else:
                st.error("Contact name cannot be empty.")
    
    # Welcome message and feedback
    st.markdown("---")
    st.markdown("### 💙 You're About to Transform Your Relationships")
    st.info("""
    **The Third Voice AI** helps you navigate emotionally charged conversations with wisdom and love.
    
    Whether someone just hurt you, or you're struggling to express yourself without causing pain — 
    we're here to be that calm, healing voice when both people are speaking from pain.
    """)
    
    # Add feedback widget for first-time experience
    show_feedback_widget("first_time_setup")


def render_contacts_list_view():
    st.markdown("### 🎙️ The Third Voice - Your Contacts")
    
    if not st.session_state.contacts:
        st.info("**No contacts yet.** Add your first contact to get started!")
        if st.button("➕ Add New Contact", use_container_width=True):
            st.session_state.app_mode = "add_contact_view"
            st.rerun()
        
        # Show helpful context for new users
        st.markdown("---")
        st.markdown("### 💡 How The Third Voice Works")
        st.markdown("""
        1. **Add a contact** for someone you communicate with
        2. **Choose the relationship type** (romantic, family, work, etc.)
        3. **Share what happened** - their message or your response
        4. **Get AI guidance** - we'll help you communicate with love and healing
        """)
        return
    
    # Sort contacts by most recent activity
    sorted_contacts = sorted(
        st.session_state.contacts.items(),
        key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"],
        reverse=True
    )
    
    st.markdown(f"**{len(sorted_contacts)} contact{'s' if len(sorted_contacts) != 1 else ''}** • Tap to continue conversation")
    
    for name, data in sorted_contacts:
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start your first conversation!"
        time_str = last_msg["time"] if last_msg else "New"
        context_icon = CONTEXTS.get(data["context"], {"icon": "💬"})["icon"]
        
        if st.button(
            f"{context_icon} **{name}** • {time_str}\n_{preview}_",
            key=f"contact_{name}",
            use_container_width=True
        ):
            st.session_state.active_contact = name
            st.session_state.app_mode = "conversation_view"
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.app_mode = "add_contact_view"
        st.rerun()
    
    # Add feedback widget for contacts experience
    show_feedback_widget("contacts_list")


# === MAIN EXECUTION ===
if __name__ == "__main__":
    # Configure page first
    configure_page()
    
    # Initialize session state
    init_session_state()
    
    # Render sidebar (only when authenticated)
    render_sidebar()
    
    # Run main application
    main_app()
