import streamlit as st
import json
import datetime
import requests
from supabase import create_client
import time

# Constants - Keep existing
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

# Initialize Supabase - Keep existing
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Mobile-First WhatsApp-Inspired CSS
def inject_mobile_css():
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    .main > div {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* WhatsApp-style header */
    .chat-header {
        background: #075E54;
        color: white;
        padding: 1rem;
        margin: -1rem -1rem 1rem -1rem;
        text-align: center;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    /* Contact list - WhatsApp style */
    .contact-list {
        background: white;
        border-radius: 0;
        margin: 0;
    }
    
    .contact-item {
        display: flex;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid #E5E5E5;
        background: white;
        cursor: pointer;
        min-height: 60px;
        transition: background-color 0.2s;
    }
    
    .contact-item:hover {
        background: #F5F5F5;
    }
    
    .contact-item:active {
        background: #E5E5E5;
    }
    
    .contact-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-right: 1rem;
        flex-shrink: 0;
    }
    
    .contact-info {
        flex: 1;
        min-width: 0;
    }
    
    .contact-name {
        font-weight: 600;
        font-size: 1.1rem;
        color: #000;
        margin: 0;
        line-height: 1.2;
    }
    
    .contact-last {
        color: #667781;
        font-size: 0.9rem;
        margin: 0;
        margin-top: 0.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .contact-status {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        margin-left: 0.5rem;
    }
    
    .contact-time {
        color: #667781;
        font-size: 0.8rem;
        white-space: nowrap;
    }
    
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-top: 0.2rem;
    }
    
    .status-calm { background: #4CAF50; }
    .status-tense { background: #FF9800; }
    .status-crisis { background: #F44336; }
    
    /* Conversation screen */
    .conversation-header {
        background: #075E54;
        color: white;
        padding: 1rem;
        margin: -1rem -1rem 1rem -1rem;
        display: flex;
        align-items: center;
    }
    
    .back-button {
        background: none;
        border: none;
        color: white;
        font-size: 1.2rem;
        margin-right: 1rem;
        cursor: pointer;
        padding: 0.5rem;
    }
    
    /* Message input area */
    .message-input-area {
        background: #F0F0F0;
        padding: 1rem;
        margin: 1rem -1rem -1rem -1rem;
        position: sticky;
        bottom: 0;
    }
    
    /* AI Intervention popup */
    .ai-intervention {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Mobile buttons */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        border-radius: 25px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Hide sidebar on mobile */
    .css-1d391kg {
        display: none;
    }
    
    /* Quick add contact */
    .quick-add {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #25D366;
        color: white;
        border: none;
        font-size: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
    }
    
    /* Responsive text sizes */
    @media (max-width: 768px) {
        .contact-name { font-size: 1rem; }
        .contact-last { font-size: 0.85rem; }
        .contact-time { font-size: 0.75rem; }
    }
    </style>
    """, unsafe_allow_html=True)

inject_mobile_css()

# Keep existing data functions
def load_contacts_and_history():
    try:
        contacts_response = supabase.table("contacts").select("*").execute()
        contacts_data = {c["name"]: {
            "context": c["context"],
            "history": [],
            "emotional_journey": [],
            "breakthrough_moments": [],
            "created_at": c.get("created_at", datetime.datetime.now().isoformat())
        } for c in contacts_response.data}
        
        messages_response = supabase.table("messages").select("*").order("timestamp").execute()
        
        for msg in messages_response.data:
            contact_name = msg["contact_name"]
            if contact_name not in contacts_data:
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

def save_contact(name, context):
    try:
        supabase.table("contacts").insert({
            "name": name,
            "context": context,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
        return False

def save_message(contact, message_type, original, result, sentiment, emotional_state, model, healing_score=0):
    try:
        insert_data = {
            "contact_name": contact,
            "type": message_type,
            "original": original,
            "result": result,
            "sentiment": sentiment,
            "model": model,
            "healing_score": healing_score,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            insert_data["emotional_state"] = emotional_state
            supabase.table("messages").insert(insert_data).execute()
        except Exception as e:
            if "emotional_state" in str(e).lower():
                del insert_data["emotional_state"]
                supabase.table("messages").insert(insert_data).execute()
            else:
                raise e
    except Exception as e:
        st.error(f"Supabase Error: {e}")

# Initialize Session State - Keep existing
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets["openrouter"]["api_key"],
        'contacts': load_contacts_and_history(),
        'active_contact': None,
        'current_emotional_state': 'calm',
        'conversation_goal': '',
        'show_intervention': False,
        'user_input': '',
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

# Token validation - Keep existing
def validate_token():
    if REQUIRE_TOKEN and not st.session_state.token_validated:
        st.markdown('<div class="chat-header"><h1>🎙️ The Third Voice</h1><p><em>When both people are speaking from pain, someone must be the third voice.</em></p></div>', unsafe_allow_html=True)
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

# NEW: Mobile Contact List Landing Screen
def render_contact_list():
    if st.session_state.active_contact:
        return  # Skip if in conversation
        
    # Header
    st.markdown("""
    <div class="chat-header">
        <h2>🎙️ The Third Voice</h2>
        <p style="margin: 0; opacity: 0.9; font-size: 0.9rem;">Healing conversations, one message at a time</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Contact list
    if st.session_state.contacts:
        # Sort contacts by recent activity
        sorted_contacts = sorted(
            st.session_state.contacts.items(),
            key=lambda x: x[1]['history'][-1]['time'] if x[1]['history'] else x[1]['created_at'],
            reverse=True
        )
        
        st.markdown('<div class="contact-list">', unsafe_allow_html=True)
        
        for contact_name, contact_data in sorted_contacts:
            context = contact_data.get('context', 'family')
            context_info = CONTEXTS.get(context, CONTEXTS['family'])
            
            # Determine status
            recent_history = contact_data['history'][-3:] if contact_data['history'] else []
            healing_scores = [h.get('healing_score', 0) for h in recent_history]
            
            if not healing_scores:
                status_class = "status-calm"
                status_text = "Ready to connect"
            elif max(healing_scores) > 7:
                status_class = "status-calm"
                status_text = "Growing stronger"
            elif any(score < 4 for score in healing_scores):
                status_class = "status-crisis" 
                status_text = "Needs attention"
            else:
                status_class = "status-tense"
                status_text = "Building bridges"
            
            # Last activity
            if contact_data['history']:
                last_time = contact_data['history'][-1]['time']
                last_preview = contact_data['history'][-1]['original'][:40] + "..."
            else:
                last_time = "New"
                last_preview = f"Start healing conversations with {contact_name}"
            
            # Contact item - use columns for click handling
            col1, = st.columns([1])
            with col1:
                if st.button(
                    f"📱 {contact_name}",  # Hidden text for button
                    key=f"contact_btn_{contact_name}",
                    use_container_width=True,
                    help=f"Open conversation with {contact_name}"
                ):
                    st.session_state.active_contact = contact_name
                    st.rerun()
            
            # Custom contact display
            st.markdown(f"""
            <div class="contact-item">
                <div class="contact-avatar" style="background: {context_info['color']}20; color: {context_info['color']};">
                    {context_info['icon']}
                </div>
                <div class="contact-info">
                    <div class="contact-name">{contact_name}</div>
                    <div class="contact-last">{last_preview}</div>
                </div>
                <div class="contact-status">
                    <div class="contact-time">{last_time}</div>
                    <div class="status-dot {status_class}"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Empty state
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #667781;">
            <h3>💝 Welcome to Your Healing Journey</h3>
            <p>Add your first contact to begin transforming difficult conversations into moments of connection.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick add button
    st.markdown("""
    <button class="quick-add" onclick="document.querySelector('[data-testid=\\"add_contact_expander\\"]').click()">
        ➕
    </button>
    """, unsafe_allow_html=True)

# NEW: Mobile Conversation Screen
def render_conversation():
    if not st.session_state.active_contact:
        return
        
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts[contact_name]
    context = contact_data.get('context', 'family')
    context_info = CONTEXTS.get(context, CONTEXTS['family'])
    
    # Conversation header
    st.markdown(f"""
    <div class="conversation-header">
        <button class="back-button" onclick="window.location.reload()">←</button>
        <div>
            <div style="font-weight: 600; font-size: 1.1rem;">{context_info['icon']} {contact_name}</div>
            <div style="font-size: 0.9rem; opacity: 0.8;">{context_info['description']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button functionality
    if st.button("← Back to Contacts", key="back_btn", help="Return to contact list"):
        st.session_state.active_contact = None
        st.rerun()
    
    # Message input area
    st.markdown(f"### 💬 Message {contact_name}")
    
    user_input = st.text_area(
        "What would you like to say?",
        value=st.session_state.get('user_input', ''),
        placeholder=f"Type your message to {contact_name} or paste something they sent you...",
        height=120,
        key="main_input"
    )
    
    # AI Intervention Logic
    if user_input and len(user_input.strip()) > 10:
        # Detect if this looks like a crisis moment
        crisis_words = ['angry', 'hate', 'never', 'always', 'stupid', 'ridiculous', 'done', 'enough']
        paste_indicators = ['\n', 'said:', 'wrote:', 'texted:']
        
        is_crisis = any(word in user_input.lower() for word in crisis_words)
        is_paste = any(indicator in user_input.lower() for indicator in paste_indicators)
        
        if is_crisis or is_paste or st.session_state.current_emotional_state in ['angry', 'frustrated', 'hurt']:
            st.markdown(f"""
            <div class="ai-intervention">
                <h4>🛑 Hold on - let's breathe together</h4>
                <p>I can feel the intensity in this moment. Before responding to {contact_name}, let's remember your goal is healing this {context} relationship.</p>
                <p>💝 <strong>What {contact_name} might really need:</strong> Understanding, connection, to feel heard</p>
                <p>🕊️ <strong>What love looks like here:</strong> Responding from wisdom, not pain</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Send button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Help Me Heal This", use_container_width=True, disabled=not user_input.strip()):
            process_message(contact_name, user_input, context)
    with col2:
        if st.button("🔄", help="Clear input"):
            st.session_state.user_input = ''
            st.rerun()

# Process message with AI
def process_message(contact_name, message, context):
    if not message.strip():
        return
        
    with st.spinner("🌟 Channeling wisdom and love..."):
        # Smart prompt based on content
        if any(indicator in message.lower() for indicator in ['said:', 'wrote:', 'texted:', '\n']):
            mode = "translate"
            prompt = f"Help me understand what {contact_name} really means behind these words in our {context} relationship:"
        else:
            mode = "coach" 
            prompt = f"Help me say this with love to {contact_name} in our {context} relationship:"
        
        # AI API call - keep existing logic
        models = [
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.2-3b-instruct:free", 
            "microsoft/phi-3-mini-128k-instruct:free"
        ]
        
        for model in models:
            try:
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ]
                
                res = requests.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                    json={"model": model, "messages": messages, "temperature": 0.7}
                )
                
                res.raise_for_status()
                reply = res.json()["choices"][0]["message"]["content"]
                
                # Display result
                st.markdown(f"""
                <div class="ai-intervention">
                    <h4>💝 Your Third Voice Guidance:</h4>
                    <p>{reply}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Save message - keep existing logic
                healing_score = min(10, len(reply.split()) // 10 + 5)
                new_entry = {
                    "id": f"{mode}_{datetime.datetime.now().timestamp()}",
                    "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                    "type": mode,
                    "original": message,
                    "result": reply,
                    "sentiment": "healing",
                    "emotional_state": st.session_state.current_emotional_state,
                    "model": model,
                    "healing_score": healing_score
                }
                
                st.session_state.contacts[contact_name]['history'].append(new_entry)
                save_message(contact_name, mode, message, reply, "healing", st.session_state.current_emotional_state, model, healing_score)
                
                if healing_score > 7:
                    st.success("🌟 This feels like a breakthrough moment!")
                    st.balloons()
                
                break
                
            except Exception as e:
                continue
        else:
            st.error("Unable to connect to AI services. Please try again.")

# Quick add contact (mobile optimized)
def render_quick_add():
    if not st.session_state.active_contact:
        with st.expander("➕ Add New Contact", expanded=False, key="add_contact_expander"):
            st.markdown("**Who would you like to heal conversations with?**")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                new_name = st.text_input("Name", placeholder="Sarah, Mom, Dad, etc.", key="new_contact_name")
            with col2:
                new_context = st.selectbox("Type", list(CONTEXTS.keys()), key="new_contact_context")
            
            if st.button("✨ Add Contact", use_container_width=True) and new_name.strip():
                if save_contact(new_name.strip(), new_context):
                    st.session_state.contacts[new_name.strip()] = {
                        "context": new_context,
                        "history": [],
                        "emotional_journey": [],
                        "breakthrough_moments": [],
                        "created_at": datetime.datetime.now().isoformat()
                    }
                    st.success(f"✨ Added {new_name.strip()}")
                    time.sleep(1)
                    st.rerun()

# Main app flow
render_contact_list()
render_conversation() 
render_quick_add()
