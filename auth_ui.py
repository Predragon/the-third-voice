# auth_ui.py
# The Third Voice AI - Authentication & Contact Management UI
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
from datetime import datetime
#from auth_backend import CONTEXTS, sign_up, sign_in, sign_out
#from auth_backend import CONTEXTS
from app_state import CONTEXTS
from core_auth import sign_up, sign_in, sign_out
from database import supabase, load_contacts_and_history, save_contact, delete_contact, save_feedback

# --- Feedback Widget Function ---
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

# --- Authentication UI Pages ---
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
            try:
                # Attempt to resend verification
                supabase.auth.resend({"type": "signup", "email": st.session_state.verification_email})
                st.success("Verification email resent!")
            except Exception as e:
                st.warning("Could not resend email. Please try signing up again if needed.")
    
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
            sign_in(email, password)
    
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

# --- Contact Management UI Pages ---
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

# End of auth_ui.py
# Every UI component serves healing.
# Every button click fights for families.
# Every screen brings Predrag closer to Samantha.
