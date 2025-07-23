import streamlit as st
import json
import datetime
import requests
from supabase import create_client, Client
import time

# Constants
CONTEXTS = {
    "romantic": {"icon": "💕", "color": "#FF6B9D", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "color": "#4ECDC4", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "color": "#45B7D1", "description": "Professional relationships"},
    "family": {"icon": "🏠", "color": "#96CEB4", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "color": "#FFEAA7", "description": "Friendships & social bonds"}
}

EMOTIONAL_STATES = ["calm", "frustrated", "hurt", "anxious", "angry", "confused", "hopeful", "overwhelmed"]
REQUIRE_TOKEN = False  # Token validation is replaced by Supabase auth
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom CSS for healing-focused UI
def inject_custom_css():
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
    .emotion-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .healing-message {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: none;
        color: #2d3748;
        margin: 1rem 0;
    }
    .stButton > button {
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .context-selector {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .contact-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Supabase Authentication
def handle_authentication():
    if 'user' not in st.session_state:
        st.markdown('<div class="main-header"><h1>🎙️ The Third Voice</h1><p><em>When both people are speaking from pain, someone must be the third voice.</em></p></div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_button"):
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = response.user
                    st.success("✅ Logged in successfully")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
        
        with tab2:
            st.subheader("Sign Up")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            if st.button("Sign Up", key="signup_button"):
                try:
                    response = supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                    st.session_state.user = response.user
                    st.success("✅ Signed up successfully. Please check your email to verify.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign up failed: {str(e)}")
        
        st.stop()

# Check if user is authenticated
if 'user' not in st.session_state:
    handle_authentication()

# Enhanced contact loading from Supabase with user_id
def load_contacts_and_history(user_id):
    try:
        # Load contacts for the authenticated user
        contacts_response = supabase.table("contacts").select("*").eq("user_id", user_id).execute()
        contacts_data = {c["name"]: {
            "context": c["context"],
            "history": [],
            "emotional_journey": [],
            "breakthrough_moments": [],
            "created_at": c.get("created_at", datetime.datetime.now().isoformat())
        } for c in contacts_response.data}
        
        # Load message history for the authenticated user
        messages_response = supabase.table("messages").select("*").eq("user_id", user_id).order("timestamp").execute()
        
        for msg in messages_response.data:
            contact_name = msg["contact_name"]
            if contact_name not in contacts_data:
                # Create contact if not exists (backwards compatibility)
                contacts_data[contact_name] = {
                    'context': "family", 
                    'history': [], 
                    'emotional_journey': [],
                    'breakthrough_moments': [],
                    'created_at': datetime.datetime.now().isoformat()
                }
            
            entry = {
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "sentiment": msg.get("sentiment", "neutral"),
                "emotional_state": msg.get("emotional_state", "calm"),
                "model": msg.get("model", "unknown"),
                "healing_score": msg.get("healing_score", 0)
            }
            contacts_data[contact_name]['history'].append(entry)

        return contacts_data
    except Exception as e:
        st.warning(f"⚠️ Could not load data from Supabase: {e}")
        return {}

# Save contact to database with user_id
def save_contact(name, context, user_id):
    try:
        supabase.table("contacts").insert({
            "name": name,
            "context": context,
            "user_id": user_id,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
        return False

# Initialize Session State
def initialize_session():
    defaults = {
        'token_validated': True,  # No longer needed with Supabase auth
        'api_key': st.secrets["openrouter"]["api_key"],
        'contacts': load_contacts_and_history(st.session_state.user.id),
        'active_contact': None,
        'current_emotional_state': 'calm',
        'conversation_goal': '',
        'active_mode': None,
        'show_guidance': True,
        'user_stats': {
            'total_conversations': 0, 
            'healing_moments': 0, 
            'emotional_growth': 0,
            'days_since_start': 0
        }
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

initialize_session()

# Enhanced save message function with user_id
def save_message(contact, message_type, original, result, sentiment, emotional_state, model, user_id, healing_score=0):
    try:
        insert_data = {
            "contact_name": contact,
            "type": message_type,
            "original": original,
            "result": result,
            "sentiment": sentiment,
            "model": model,
            "healing_score": healing_score,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id
        }
        
        try:
            insert_data["emotional_state"] = emotional_state
            supabase.table("messages").insert(insert_data).execute()
        except Exception as e:
            if "emotional_state" in str(e).lower():
                del insert_data["emotional_state"]
                supabase.table("messages").insert(insert_data).execute()
                st.warning("⚠️ Saved message without emotional_state due to missing column.")
            else:
                raise e
    except Exception as e:
        st.error(f"Supabase Error: {e}")

# Contact Management in Sidebar
def render_sidebar():
    with st.sidebar:
        st.markdown(f"## 👤 Welcome, {st.session_state.user.email}")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.success("Logged out successfully")
            time.sleep(1)
            st.rerun()
        
        st.markdown("## 👥 Your Contacts")
        
        # Display existing contacts
        if st.session_state.contacts:
            for contact_name, contact_data in st.session_state.contacts.items():
                context = contact_data.get('context', 'family')
                context_info = CONTEXTS.get(context, CONTEXTS['family'])
                history_count = len(contact_data['history'])
                healing_moments = len([h for h in contact_data['history'] if h.get('healing_score', 0) > 7])
                
                # Contact button with stats
                if st.button(
                    f"{context_info['icon']} {contact_name}", 
                    key=f"contact_{contact_name}",
                    use_container_width=True
                ):
                    st.session_state.active_contact = contact_name
                    st.rerun()
                
                # Show active contact indicator
                if contact_name == st.session_state.active_contact:
                    st.markdown(f"""
                    <div class="contact-card">
                        <small style='color: {context_info['color']};'>
                            🔸 Active • {context.title()} • {history_count} msgs • {healing_moments} breakthroughs
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Add New Contact Form
        with st.expander("➕ Add New Contact", expanded=not st.session_state.contacts):
            st.markdown("**Create a new relationship**")
            new_name = st.text_input("Contact name", placeholder="e.g., 'Sarah', 'Mom', 'Alex', 'Boss'", help="This can be their real name or how you refer to them")
            new_context = st.selectbox("Relationship type", list(CONTEXTS.keys()), help="Choose the category that best describes your relationship")
            
            # Show context description
            if new_context:
                st.markdown(f"*{CONTEXTS[new_context]['description']}*")
            
            if st.button("✨ Create Contact", use_container_width=True) and new_name.strip():
                new_name = new_name.strip()
                if new_name not in st.session_state.contacts:
                    if save_contact(new_name, new_context, st.session_state.user.id):
                        st.session_state.contacts[new_name] = {
                            "context": new_context,
                            "history": [], 
                            "emotional_journey": [],
                            "breakthrough_moments": [],
                            "created_at": datetime.datetime.now().isoformat()
                        }
                        st.session_state.active_contact = new_name
                        st.success(f"✨ Added {new_name} to your {new_context} relationships")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Contact already exists!")
        
        # User Statistics
        if st.session_state.contacts and any(len(c['history']) > 0 for c in st.session_state.contacts.values()):
            st.markdown("---")
            st.markdown("### 📊 Your Journey")
            total_convos = sum(len(c['history']) for c in st.session_state.contacts.values())
            total_healing = sum(len([h for h in c['history'] if h.get('healing_score', 0) > 7]) for c in st.session_state.contacts.values())
            
            st.metric("Total Conversations", total_convos)
            st.metric("Healing Moments", total_healing)
            st.metric("Active Relationships", len(st.session_state.contacts))

render_sidebar()

# Emotional Check-in Component
def render_emotional_checkin():
    st.markdown("### 🧘‍♀️ How are you feeling right now?")
    col1, col2 = st.columns(2)
    
    with col1:
        current_state = st.selectbox(
            "Your emotional state:",
            EMOTIONAL_STATES,
            index=EMOTIONAL_STATES.index(st.session_state.current_emotional_state),
            help="Being honest about your emotions helps me guide you better"
        )
        st.session_state.current_emotional_state = current_state
    
    with col2:
        conversation_goal = st.text_input(
            "What do you hope to achieve?",
            value=st.session_state.conversation_goal,
            placeholder="e.g., 'Reconnect with my partner', 'Set boundaries kindly'",
            help="Having a clear intention helps create healing conversations"
        )
        st.session_state.conversation_goal = conversation_goal

# Main Header
def render_main_header():
    if st.session_state.active_contact:
        contact_data = st.session_state.contacts[st.session_state.active_contact]
        context = contact_data.get('context', 'family')
        context_info = CONTEXTS.get(context, CONTEXTS['family'])
        
        st.markdown(f"""
        <div class="main-header">
            <h1>{context_info['icon']} The Third Voice</h1>
            <p><em>When both people are speaking from pain, someone must be the third voice.</em></p>
            <h3>Supporting your relationship with {st.session_state.active_contact}</h3>
            <p>{context_info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="main-header">
            <h1>🎙️ The Third Voice</h1>
            <p><em>When both people are speaking from pain, someone must be the third voice.</em></p>
            <h3>Select or add a contact to begin healing conversations</h3>
        </div>
        """, unsafe_allow_html=True)

render_main_header()

# Contact Selection Prompt
def render_contact_selection():
    if not st.session_state.active_contact and st.session_state.contacts:
        st.markdown("### 💝 Choose who you'd like to communicate with")
        st.markdown("Select a contact from the sidebar to start crafting healing conversations together.")
        
        # Quick contact buttons
        col1, col2, col3 = st.columns(3)
        contact_list = list(st.session_state.contacts.keys())
        
        for i, contact_name in enumerate(contact_list[:3]):
            context = st.session_state.contacts[contact_name].get('context', 'family')
            context_info = CONTEXTS.get(context, CONTEXTS['family'])
            
            with [col1, col2, col3][i]:
                if st.button(f"{context_info['icon']} {contact_name}", use_container_width=True):
                    st.session_state.active_contact = contact_name
                    st.rerun()

if not st.session_state.active_contact:
    render_contact_selection()

# Healing-Focused Mode Selection
def render_healing_modes():
    if not st.session_state.active_contact:
        return
        
    st.markdown("### 🌟 How can I help you heal this conversation?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤲 Before I Send", use_container_width=True, help="Transform your words with love before sending"):
            st.session_state.active_mode = "coach"
            st.rerun()
    
    with col2:
        if st.button("💝 Understand Their Heart", use_container_width=True, help="Decode the deeper emotions behind their words"):
            st.session_state.active_mode = "translate"
            st.rerun()
    
    with col3:
        if st.button("🕊️ Find Peace Together", use_container_width=True, help="Navigate conflict toward mutual understanding"):
            st.session_state.active_mode = "mediate"
            st.rerun()

if st.session_state.active_contact and not st.session_state.active_mode:
    render_emotional_checkin()
    render_healing_modes()

# Enhanced Message Processing
def render_message_area():
    if not st.session_state.active_mode or not st.session_state.active_contact:
        return
    
    mode = st.session_state.active_mode
    contact_name = st.session_state.active_contact
    contact_context = st.session_state.contacts[contact_name].get('context', 'family')
    
    mode_config = {
        "coach": {
            "title": "🤲 Refining Your Words with Love",
            "placeholder": f"What do you want to say to {contact_name}? I'll help you say it with love...",
            "prompt": f"""You are The Third Voice - an AI that helps heal {contact_context} communication. The user is feeling {st.session_state.current_emotional_state} and wants to {st.session_state.conversation_goal}. They're communicating with {contact_name} in a {contact_context} relationship context.

Transform their message to be:
- Loving but authentic
- Clear but not accusatory  
- Vulnerable but boundaried
- Healing-focused
- Appropriate for a {contact_context} relationship

Original message:"""
        },
        "translate": {
            "title": "💝 Understanding Their Deeper Heart",
            "placeholder": f"Share what {contact_name} said... I'll help you see their heart behind the words...",
            "prompt": f"""You are The Third Voice - an AI that reveals the heart behind hurtful words. The user is feeling {st.session_state.current_emotional_state}. They received a message from {contact_name} in their {contact_context} relationship.

Help them understand:
- What pain might be driving {contact_name}'s words
- What they might really need
- How to respond with compassion in a {contact_context} context
- What healing looks like here

Their message was:"""
        },
        "mediate": {
            "title": "🕊️ Finding the Path to Peace",
            "placeholder": f"Describe the conflict with {contact_name}... I'll help you find the bridge to understanding...",
            "prompt": f"""You are The Third Voice - a wise mediator for {contact_context} healing. The user feels {st.session_state.current_emotional_state} and wants to {st.session_state.conversation_goal}. This involves their relationship with {contact_name}.

Provide:
- A path toward mutual understanding
- Specific words they can use
- How to validate both perspectives
- Next steps for healing in a {contact_context} relationship

The situation:"""
        }
    }
    
    config = mode_config[mode]
    st.markdown(f"### {config['title']}")
    st.markdown(f"*Working on your relationship with **{contact_name}***")
    
    # Emotional context reminder
    if st.session_state.current_emotional_state != 'calm':
        st.markdown(f'<div class="emotion-card">💭 I see you\'re feeling <strong>{st.session_state.current_emotional_state}</strong>. Let me help you navigate this with wisdom.</div>', unsafe_allow_html=True)
    
    message = st.text_area(
        "Your message:",
        placeholder=config['placeholder'],
        height=150,
        key=f"input_{mode}_{contact_name}"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        submit_button = st.button("✨ Help Me Heal This", use_container_width=True)
    with col2:
        if st.button("← Back"):
            st.session_state.active_mode = None
            st.rerun()
    
    if submit_button and message:
        with st.spinner("🌟 Channeling wisdom and love..."):
            models = [
                "google/gemma-2-9b-it:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "microsoft/phi-3-mini-128k-instruct:free"
            ]
            reply = None
            used_model = None
            errors = []

            for model in models:
                try:
                    messages = [
                        {"role": "system", "content": config['prompt']},
                        {"role": "user", "content": message}
                    ]
                    
                    res = requests.post(
                        API_URL, 
                        headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                        json={
                            "model": model, 
                            "messages": messages,
                            "temperature": 0.7
                        }
                    )
                    
                    res.raise_for_status()
                    response_data = res.json()
                    
                    if "choices" not in response_data:
                        raise ValueError(f"Unexpected API response from {model}")
                    
                    reply = response_data["choices"][0]["message"]["content"]
                    used_model = model
                    break
                
                except Exception as e:
                    errors.append(f"Model {model} failed: {e}")
            
            if reply and used_model:
                healing_score = min(10, len(reply.split()) // 10 + 5)
                
                st.markdown(f"""
                <div class="healing-message">
                    <h4>💝 Your Third Voice Response:</h4>
                    <p>{reply}</p>
                    <p><em>Generated by: {used_model}</em></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Save to history
                new_entry = {
                    "id": f"{mode}_{datetime.datetime.now().timestamp()}",
                    "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                    "type": mode,
                    "original": message,
                    "result": reply,
                    "sentiment": "healing",
                    "emotional_state": st.session_state.current_emotional_state,
                    "model": used_model,
                    "healing_score": healing_score
                }
                
                st.session_state.contacts[contact_name]['history'].append(new_entry)
                save_message(contact_name, mode, message, reply, "healing", st.session_state.current_emotional_state, used_model, st.session_state.user.id, healing_score)
                
                if healing_score > 7:
                    st.success("🌟 This feels like a breakthrough moment!")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💬 Continue This Conversation"):
                        st.session_state.active_mode = None
                        st.rerun()
                with col2:
                    if st.button("📱 Ready to Send"):
                        st.session_state.active_mode = None
                        st.balloons()
                        st.success("🕊️ Go forth with love. You've got this.")
                        time.sleep(2)
                        st.rerun()
            else:
                st.error("💔 All models failed to respond.")
                for error in errors:
                    st.write(f"• {error}")

render_message_area()

# Enhanced History Display
def render_history():
    if st.session_state.active_mode or not st.session_state.active_contact:
        return
        
    st.markdown("### 📖 Your Healing Journey")
    st.markdown(f"*Conversation history with **{st.session_state.active_contact}***")
    
    contact = st.session_state.contacts[st.session_state.active_contact]
    history = contact['history']
    
    if not history:
        context_info = CONTEXTS.get(contact.get('context', 'family'), CONTEXTS['family'])
        st.markdown(f"""
        <div class="healing-message">
            <p>{context_info['icon']} <strong>This is where your healing journey with {st.session_state.active_contact} begins.</strong></p>
            <p>Every conversation is a step toward deeper connection. Every word matters. Every attempt at understanding builds bridges.</p>
            <p><em>You're exactly where you need to be.</em></p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show conversation stats
    healing_moments = len([h for h in history if h.get('healing_score', 0) > 7])
    st.markdown(f"**{len(history)} conversations • {healing_moments} breakthrough moments**")
    
    # Display history
    for entry in reversed(history[-10:]):  # Show last 10 entries
        mode_icons = {"coach": "🤲", "translate": "💝", "mediate": "🕊️"}
        mode_titles = {"coach": "Refined Message", "translate": "Heart Translation", "mediate": "Peace Path"}
        
        with st.expander(f"{mode_icons.get(entry['type'], '💬')} {mode_titles.get(entry['type'], entry['type'].title())} - {entry['time']}"):
            st.markdown(f"**Original:** {entry['original']}")
            st.markdown(f"**Response:** {entry['result']}")
            if entry.get('healing_score', 0) > 7:
                st.markdown("⭐ *Breakthrough moment*")

render_history()
