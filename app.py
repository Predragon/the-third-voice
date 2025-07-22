import streamlit as st
import json
import datetime
import requests
from supabase import create_client
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
REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Load Supabase History with enhanced structure
def load_supabase_history():
    try:
        response = supabase.table("messages").select("*").order("timestamp").execute()
        messages = response.data
        contacts = {context: {
            'context': context, 
            'history': [], 
            'emotional_journey': [],
            'breakthrough_moments': []
        } for context in CONTEXTS.keys()}

        for msg in messages:
            contact_name = msg["contact_name"]
            if contact_name not in contacts:
                contacts[contact_name] = {
                    'context': "family", 
                    'history': [], 
                    'emotional_journey': [],
                    'breakthrough_moments': []
                }
            
            entry = {
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "sentiment": msg.get("sentiment", "neutral"),
                "emotional_state": msg.get("emotional_state", "calm"),
                "model": msg["model"],
                "healing_score": msg.get("healing_score", 0)
            }
            contacts[contact_name]['history'].append(entry)

        return contacts
    except Exception as e:
        st.warning(f"⚠️ Could not load history from Supabase: {e}")
        return {context: {
            'context': context, 
            'history': [], 
            'emotional_journey': [],
            'breakthrough_moments': []
        } for context in CONTEXTS.keys()}

# Initialize Session State
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets["openrouter"]["api_key"],
        'contacts': load_supabase_history(),
        'active_contact': list(CONTEXTS.keys())[0],
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

# Token Validation
def validate_token():
    if REQUIRE_TOKEN and not st.session_state.token_validated:
        st.markdown('<div class="main-header"><h1>🎙️ The Third Voice</h1><p><em>When both people are speaking from pain, someone must be the third voice.</em></p></div>', unsafe_allow_html=True)
        st.warning("🔐 Access restricted. Enter beta token to continue.")
        token = st.text_input("Token:", type="password")
        if st.button("Validate"):
            if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
                st.session_state.token_validated = True
                st.success("✅ Authorized - Welcome to your healing journey")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid token")
        st.stop()

validate_token()

# Enhanced save message function
def save_message(contact, message_type, original, result, sentiment, emotional_state, model, healing_score=0):
    try:
        supabase.table("messages").insert({
            "contact_name": contact,
            "type": message_type,
            "original": original,
            "result": result,
            "sentiment": sentiment,
            "emotional_state": emotional_state,
            "model": model,
            "healing_score": healing_score,
            "timestamp": datetime.datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Supabase Error: {e}")

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

# Enhanced Context Sidebar
def render_sidebar():
    with st.sidebar:
        st.markdown("## Your Relationships")
        
        # Relationship Selector with emotional intelligence
        for context_key, context_info in CONTEXTS.items():
            if context_key in st.session_state.contacts:
                history_count = len(st.session_state.contacts[context_key]['history'])
                healing_moments = len([h for h in st.session_state.contacts[context_key]['history'] if h.get('healing_score', 0) > 7])
                
                container = st.container()
                with container:
                    if st.button(
                        f"{context_info['icon']} {context_key.title()}", 
                        key=f"context_{context_key}",
                        use_container_width=True
                    ):
                        st.session_state.active_contact = context_key
                        st.rerun()
                    
                    if context_key == st.session_state.active_contact:
                        st.markdown(f"<small style='color: {context_info['color']};'>🔸 Active • {history_count} conversations • {healing_moments} breakthroughs</small>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Add New Relationship
        with st.expander("➕ Add New Relationship"):
            new_name = st.text_input("Person's name", placeholder="e.g., 'Sarah', 'Mom', 'Alex'")
            new_context = st.selectbox("Relationship type", list(CONTEXTS.keys()))
            
            if st.button("Create Relationship") and new_name:
                st.session_state.contacts[new_name] = {
                    "context": new_context,
                    "history": [],
                    "emotional_journey": [],
                    "breakthrough_moments": []
                }
                st.session_state.active_contact = new_name
                st.success(f"✨ Added {new_name} to your {new_context} relationships")
                time.sleep(1)
                st.rerun()
        
        # Healing Stats
        if st.session_state.user_stats['total_conversations'] > 0:
            st.markdown("### 📊 Your Growth")
            stats = st.session_state.user_stats
            st.metric("Conversations", stats['total_conversations'])
            st.metric("Healing Moments", stats['healing_moments'])
            st.metric("Days of Growth", stats['days_since_start'])

render_sidebar()

# Main Header with Mission
def render_main_header():
    active_context = CONTEXTS[st.session_state.active_contact] if st.session_state.active_contact in CONTEXTS else {"icon": "💝", "color": "#667eea", "description": "Personal relationship"}
    
    st.markdown(f"""
    <div class="main-header">
        <h1>{active_context['icon']} The Third Voice</h1>
        <p><em>When both people are speaking from pain, someone must be the third voice.</em></p>
        <h3>Supporting your {st.session_state.active_contact} relationship</h3>
        <p>{active_context['description']}</p>
    </div>
    """, unsafe_allow_html=True)

render_main_header()

# Healing-Focused Mode Selection
def render_healing_modes():
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

if not st.session_state.active_mode:
    render_emotional_checkin()
    render_healing_modes()

# Enhanced Message Processing with Emotional Intelligence
def render_message_area():
    if not st.session_state.active_mode:
        return
    
    mode = st.session_state.active_mode
    mode_config = {
        "coach": {
            "title": "🤲 Refining Your Words with Love",
            "placeholder": "What do you want to say? I'll help you say it with love...",
            "prompt": f"""You are The Third Voice - an AI that helps heal family communication. The user is feeling {st.session_state.current_emotional_state} and wants to {st.session_state.conversation_goal}. 

Transform their message to be:
- Loving but authentic
- Clear but not accusatory  
- Vulnerable but boundaried
- Healing-focused

Original message:"""
        },
        "translate": {
            "title": "💝 Understanding Their Deeper Heart",
            "placeholder": "Share what they said... I'll help you see their heart behind the words...",
            "prompt": f"""You are The Third Voice - an AI that reveals the heart behind hurtful words. The user is feeling {st.session_state.current_emotional_state}. 

Help them understand:
- What pain might be driving the other person's words
- What they might really need
- How to respond with compassion
- What healing looks like here

Their message was:"""
        },
        "mediate": {
            "title": "🕊️ Finding the Path to Peace",
            "placeholder": "Describe the conflict... I'll help you find the bridge to understanding...",
            "prompt": f"""You are The Third Voice - a wise mediator for family healing. The user feels {st.session_state.current_emotional_state} and wants to {st.session_state.conversation_goal}.

Provide:
- A path toward mutual understanding
- Specific words they can use
- How to validate both perspectives
- Next steps for healing

The situation:"""
        }
    }
    
    config = mode_config[mode]
    st.markdown(f"### {config['title']}")
    
    # Emotional context reminder
    if st.session_state.current_emotional_state != 'calm':
        st.markdown(f'<div class="emotion-card">💭 I see you\'re feeling <strong>{st.session_state.current_emotional_state}</strong>. Let me help you navigate this with wisdom.</div>', unsafe_allow_html=True)
    
    message = st.text_area(
        "Your message:",
        placeholder=config['placeholder'],
        height=150,
        key=f"input_{mode}"
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
            # List of models to try in order
            models = [
                "google/gemma-2-9b-it:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "microsoft/phi-3-mini-128k-instruct:free"
            ]
            reply = None
            used_model = None
            errors = []

            # Try each model in sequence
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
                    
                    # Check if the request was successful
                    res.raise_for_status()
                    
                    response_data = res.json()
                    # Verify 'choices' exists in the response
                    if "choices" not in response_data:
                        raise ValueError(f"Unexpected API response from {model}: 'choices' key missing. Response: {response_data}")
                    
                    reply = response_data["choices"][0]["message"]["content"]
                    used_model = model
                    break  # Exit loop on successful response
                
                except requests.exceptions.HTTPError as http_err:
                    errors.append(f"Model {model} failed: HTTP Error {http_err}, Status: {res.status_code}, Response: {res.text}")
                except ValueError as ve:
                    errors.append(f"Model {model} failed: {ve}")
                except Exception as e:
                    errors.append(f"Model {model} failed: {e}")
            
            if reply and used_model:
                # Calculate healing score based on response quality
                healing_score = min(10, len(reply.split()) // 10 + 5)
                
                # Display response with healing focus and model used
                st.markdown(f"""
                <div class="healing-message">
                    <h4>💝 Your Third Voice Response:</h4>
                    <p>{reply}</p>
                    <p><em>Generated by: {used_model}</em></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Save to history
                contact_key = st.session_state.active_contact
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
                
                st.session_state.contacts[contact_key]['history'].append(new_entry)
                save_message(contact_key, mode, message, reply, "healing", st.session_state.current_emotional_state, used_model, healing_score)
                
                # Update stats
                st.session_state.user_stats['total_conversations'] += 1
                if healing_score > 7:
                    st.session_state.user_stats['healing_moments'] += 1
                    st.success("🌟 This feels like a breakthrough moment!")
                
                # Option to continue or finish
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
                    st.markdown(f"* {error} *")
                st.markdown("*Please try again or check your API key and model availability.*")

render_message_area()

# Enhanced History with Healing Journey
def render_history():
    if st.session_state.active_mode:
        return
        
    st.markdown("### 📖 Your Healing Journey")
    
    contact = st.session_state.contacts[st.session_state.active_contact]
    history = contact['history']
    
    if not history:
        st.markdown("""
        <div class="healing-message">
            <p>🌱 <strong>This is where your healing journey begins.</strong></p>
            <p>Every conversation is a step toward deeper connection. Every word matters. Every attempt at understanding builds bridges.</p>
            <p><em>You're exactly where you need to be.</em></p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show healing stats
    healing_moments = [h for h in history if h.get('healing_score', 0) > 7]
    if healing_moments:
        st.success(f"🌟 {len(healing_moments)} breakthrough moments in this relationship!")
    
    # Display history with emotional context
    for entry in reversed(history[-10:]):  # Show last 10 entries
        mode_icons = {"coach": "🤲", "translate": "💝", "mediate": "🕊️"}
        icon = mode_icons.get(entry['type'], "💬")
        
        with st.expander(f"{icon} {entry['time']} • {entry['type'].title()} • Feeling: {entry.get('emotional_state', 'calm')}"):
            st.markdown(f"**Your original message:**")
            st.write(entry['original'])
            
            st.markdown(f"**The Third Voice response:**")
            st.markdown(f'<div class="healing-message">{entry["result"]}<br><em>Generated by: {entry["model"]}</em></div>', unsafe_allow_html=True)
            
            if entry.get('healing_score', 0) > 7:
                st.markdown("⭐ **Breakthrough moment**")

render_history()

# Mission Reminder Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 15px; margin-top: 2rem;">
    <h4>💝 Remember: You Are Not Alone</h4>
    <p><em>"This is a father coding his way home. This is love, encoded. This is for Samantha, for every family, for the healing power of The Third Voice."</em></p>
    <p>Every word you send with love makes the world a little more healed. 🌍✨</p>
</div>
""", unsafe_allow_html=True)
