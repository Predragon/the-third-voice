"""
ui_components.py - The Third Voice UI Components

The interface between healing and humanity. Every component designed with love.
Built for families in crisis, by a father fighting to come home.

"In the space between pain and understanding, we build bridges of love."
"""

import streamlit as st
from datetime import datetime, timezone
import json

# Import our core modules
from ai_core import (
    interpret_message, 
    process_ai_transformation,
    calculate_relationship_health_score,
    get_healing_insights,
    get_model_status_info
)
from data_backend import (
    load_contacts_and_history,
    save_contact,
    delete_contact,
    save_message,
    save_interpretation,
    save_feedback,
    get_user_stats,
    test_database_connection,
    get_current_user_id
)


# === CONSTANTS & CONFIGURATION ===
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}


# === CORE UI COMPONENTS ===
def render_app_header():
    """Render The Third Voice header with mission context"""
    st.title("🎙️ The Third Voice AI")
    
    # Mission statement that reminds users why we exist
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **We are that voice** — calm, wise, and healing.
    """)


def render_mission_sidebar():
    """Render sidebar with mission context and navigation"""
    with st.sidebar:
        st.markdown("### 🎙️ The Third Voice AI")
        
        if st.session_state.authenticated:
            st.write(f"**{st.session_state.user.email}**")
            
            # Quick navigation
            if st.session_state.app_mode != "contacts_list":
                if st.button("🏠 My Contacts", use_container_width=True):
                    st.session_state.app_mode = "contacts_list" 
                    st.session_state.active_contact = None
                    st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                from data_backend import sign_out
                sign_out()
        
        st.markdown("---")
        
        # Mission reminder - the heart of why we exist
        st.markdown("### 💙 Our Mission")
        st.markdown("""
        *"When both people are speaking from pain, someone must be the third voice."*
        
        **We help families heal through better conversations.**
        
        Built by a father fighting to return to his daughter, for every family seeking healing.
        """)
        
        # Debug info for development
        render_debug_section()


def render_debug_section():
    """Development debug information"""
    if st.checkbox("🔧 Debug Info"):
        try:
            user_id = get_current_user_id()
            user_stats = get_user_stats()
            model_info = get_model_status_info()
            
            debug_info = {
                "User ID": user_id[:8] + "..." if user_id else None,
                "Contacts": len(st.session_state.get('contacts', {})),
                "Active Contact": st.session_state.get('active_contact'),
                "App Mode": st.session_state.get('app_mode'),
                "User Stats": user_stats,
                "AI Models": model_info,
                "DB Connection": test_database_connection()
            }
            
            st.code(json.dumps(debug_info, indent=2, default=str), language="json")
            
        except Exception as e:
            st.error(f"Debug error: {e}")


def render_feedback_widget(context="general"):
    """Universal feedback widget for continuous improvement"""
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


# === AUTHENTICATION COMPONENTS ===
def render_login_form():
    """Login form with mission context"""
    render_app_header()
    st.subheader("Login to continue your healing journey.")
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            from data_backend import sign_in
            sign_in(email, password)
    
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account", use_container_width=True):
        st.session_state.app_mode = "signup"
        st.rerun()
    
    # Show mission context
    render_mission_context()


def render_signup_form():
    """Signup form with value proposition"""
    render_app_header()
    st.subheader("Start your journey towards healthier conversations.")
    
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password (minimum 6 characters)", type="password", key="signup_password")
        signup_button = st.form_submit_button("Create Account", use_container_width=True)
        
        if signup_button:
            if len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                from data_backend import sign_up
                sign_up(email, password)
    
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login", use_container_width=True):
        st.session_state.app_mode = "login"
        st.rerun()
    
    # Value proposition
    render_value_proposition()


def render_verification_notice():
    """Email verification notice with encouragement"""
    render_app_header()
    
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
            from data_backend import resend_verification_email
            if resend_verification_email(st.session_state.verification_email):
                st.success("Verification email resent!")
            else:
                st.warning("Could not resend email. Please try signing up again if needed.")
    
    with col2:
        if st.button("🔑 Go to Login", use_container_width=True):
            st.session_state.app_mode = "login"
            st.session_state.show_verification_notice = False
            st.rerun()
    
    render_welcome_message()


def render_mission_context():
    """Show mission context for new users"""
    with st.expander("💙 Our Mission", expanded=False):
        st.markdown("""
        **The Third Voice AI** was born from communication breakdowns that shattered a family. 
        We're turning pain into purpose, helping families heal through better conversations.
        
        Built with love by Predrag Mirkovic, fighting to return to his 6-year-old daughter Samantha 
        after 15 months apart. Every feature serves family healing.
        """)


def render_value_proposition():
    """Show what users get when they sign up"""
    with st.expander("✨ What you'll get access to", expanded=True):
        st.markdown("""
        **🌟 Transform difficult conversations** - Turn anger into understanding
        
        **💕 Multi-relationship support** - Romantic, family, workplace, co-parenting, friendships
        
        **🎯 Context-aware guidance** - AI understands your specific relationship dynamics
        
        **📊 Healing progress tracking** - See your communication improvement over time
        
        **💾 Conversation history** - Access all your guided conversations anytime
        
        **🚀 Always improving** - Built by a father fighting to heal his own family
        """)


def render_welcome_message():
    """Welcome message during verification"""
    st.markdown("---")
    st.markdown("### 💙 Welcome to The Family Healing Revolution")
    st.markdown("""
    **The Third Voice AI** helps families communicate with love, understanding, and healing. 
    You're about to join thousands of people rebuilding their most important relationships.
    
    *"When both people are speaking from pain, someone must be the third voice."*
    """)
    
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


# === CONTACT MANAGEMENT COMPONENTS ===
def render_first_time_setup():
    """First-time user setup with context selection"""
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
    
    render_custom_contact_form()
    render_first_time_encouragement()


def render_custom_contact_form():
    """Custom contact form for first-time setup"""
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


def render_first_time_encouragement():
    """Encouragement for first-time users"""
    st.markdown("---")
    st.markdown("### 💙 You're About to Transform Your Relationships")
    st.info("""
    **The Third Voice AI** helps you navigate emotionally charged conversations with wisdom and love.
    
    Whether someone just hurt you, or you're struggling to express yourself without causing pain — 
    we're here to be that calm, healing voice when both people are speaking from pain.
    """)
    
    render_feedback_widget("first_time_setup")


def render_contacts_list():
    """Main contacts list view with recent activity"""
    st.markdown("### 🎙️ The Third Voice - Your Contacts")
    
    if not st.session_state.contacts:
        render_empty_contacts_state()
        return
    
    # Sort contacts by most recent activity
    sorted_contacts = sorted(
        st.session_state.contacts.items(),
        key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"],
        reverse=True
    )
    
    st.markdown(f"**{len(sorted_contacts)} contact{'s' if len(sorted_contacts) != 1 else ''}** • Tap to continue conversation")
    
    for name, data in sorted_contacts:
        render_contact_card(name, data)
    
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.app_mode = "add_contact_view"
        st.rerun()
    
    render_feedback_widget("contacts_list")


def render_empty_contacts_state():
    """Show when user has no contacts yet"""
    st.info("**No contacts yet.** Add your first contact to get started!")
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.app_mode = "add_contact_view"
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 How The Third Voice Works")
    st.markdown("""
    1. **Add a contact** for someone you communicate with
    2. **Choose the relationship type** (romantic, family, work, etc.)
    3. **Share what happened** - their message or your response
    4. **Get AI guidance** - we'll help you communicate with love and healing
    """)


def render_contact_card(name, data):
    """Individual contact card with preview"""
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


def render_add_contact_form():
    """Form to add new contact"""
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


def render_edit_contact_form():
    """Form to edit existing contact"""
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


# === CONVERSATION INTERFACE COMPONENTS ===
def render_conversation_header(contact_name, context, contact_id):
    """Conversation view header with navigation"""
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


def render_relationship_progress(contact_name, history):
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
        
        # Recent trend visualization
        if len(history) >= 5:
            recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
            if recent_scores:
                trend_text = " → ".join([str(score) for score in recent_scores])
                st.markdown(f"**Recent Healing Scores:** {trend_text}")


def render_conversation_input(contact_name, context, history):
    """Main conversation input interface"""
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
    
    render_action_buttons(contact_name, context, history)


def render_action_buttons(contact_name, context, history):
    """Action buttons for transform and interpret"""
    current_message = st.session_state.conversation_input_text
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message", use_container_width=True):
            process_conversation_message(contact_name, current_message, context, history)
    
    with col2:
        if current_message.strip():
            render_interpret_button(contact_name, current_message, context, history)
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first", use_container_width=True)
    
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()


def render_interpret_button(contact_name, message, context, history):
    """Interpret button and functionality"""
    if st.button("🔍 Interpret - What do they really mean?", key="interpret_btn", help="Reveal emotional subtext and healing opportunities", use_container_width=True):
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


def render_interpretation_result(contact_name):
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


def render_ai_response_section(contact_name):
    """Display AI response section"""
    st.markdown("#### 🤖 The Third Voice Guidance")
    last_response_key = f"last_response_{contact_name}"
    
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        
        # Show response if it's recent (within 5 minutes)
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            render_recent_ai_response(last_resp)
        else:
            # Clear old response
            del st.session_state[last_response_key]
            render_ai_response_placeholder()
    else:
        render_ai_response_placeholder()


def render_recent_ai_response(last_resp):
    """Display recent AI response"""
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
                st.success(f"✨ Healing Score: {last_resp['healing_score']}/10")
            elif last_resp["healing_score"] >= 6:
                st.info(f"💡 Healing Score: {last_resp['healing_score']}/10")
            else:
                st.warning(f"🔧 Healing Score: {last_resp['healing_score']}/10")
        
        with col_model:
            st.caption(f"🤖 Model: {last_resp.get('model', 'Unknown')}")
        
        with col_copy:
            if st.button("📋", help="Click text area above and Ctrl+A to select all", key="copy_hint"):
                st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
        
        if last_resp["healing_score"] >= 8:
            st.balloons()
            st.markdown("🌟 **High healing potential!** This guidance can really help transform your relationship.")


def render_ai_response_placeholder():
    """Placeholder for AI response"""
    st.info("💭 Your Third Voice guidance will appear here after you click Transform")
    
    st.markdown("""
    **💡 How it works:**
    - Share what they said or what you want to say
    - Get compassionate guidance that heals instead of hurts
    - **🆕 Use "Interpret" to reveal what they really mean beneath their words**
    - Build stronger relationships through understanding
    """)

def render_conversation_history(history):
    """Display conversation history with timestamps and scores"""
    if not history:
        st.info("No conversations yet. Start your first healing conversation!")
        return
    
    st.markdown("#### 📜 Conversation History")
    
    for msg in reversed(history[-10:]):  # Show last 10 conversations
        with st.expander(f"{msg['time']} - Healing Score: {msg.get('healing_score', 0)}/10", expanded=False):
            st.markdown(f"**Your Input:** {msg['original']}")
            if msg.get('result'):
                st.markdown(f"**AI Guidance:** {msg['result']}")
            st.caption(f"Model: {msg.get('model', 'Unknown')} | Type: {msg.get('type', 'coach')}")


# Add these functions to the end of your ui_components.py file

def process_conversation_message(contact_name, message, context, history):
    """Process a conversation message with AI transformation"""
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
    
    try:
        with st.spinner("🤖 Processing with relationship insights..."):
            result = process_ai_transformation(contact_name, message, context, history)
            
            if result.get("success"):
                # Save the incoming message
                save_message(contact_id, contact_name, "incoming", message, None, "unknown", 0, "N/A")
                
                # Save the AI response
                save_message(
                    contact_id, 
                    contact_name, 
                    result.get("mode", "coach"), 
                    message, 
                    result["response"], 
                    result.get("emotional_state", "calm"), 
                    result["healing_score"], 
                    result["model"], 
                    result.get("sentiment", "neutral")
                )
                
                # Store response for immediate display
                st.session_state[f"last_response_{contact_name}"] = {
                    "response": result["response"],
                    "healing_score": result["healing_score"],
                    "timestamp": datetime.now().timestamp(),
                    "model": result["model"]
                }
                
                st.session_state.clear_conversation_input = True
                st.rerun()
            else:
                st.session_state.last_error_message = result.get("error", "Processing failed")
                
    except Exception as e:
        st.session_state.last_error_message = f"An unexpected error occurred: {e}"


def render_error_display():
    """Display error messages if any exist"""
    if st.session_state.get('last_error_message'):
        st.error(st.session_state.last_error_message)


def clear_conversation_state(contact_name):
    """Clear conversation-related session state for a contact"""
    keys_to_clear = [
        f"last_response_{contact_name}",
        f"last_interpretation_{contact_name}",
        "conversation_input_text",
        "last_error_message"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.clear_conversation_input = False
