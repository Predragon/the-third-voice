import streamlit as st
import json
import datetime
import requests
from supabase import create_client
import time

# Constants - Enhanced with better categorization
CONTEXTS = {
    "romantic": {"icon": "💕", "color": "#FF6B9D", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "color": "#4ECDC4", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "color": "#45B7D1", "description": "Professional relationships"},
    "family": {"icon": "🏠", "color": "#96CEB4", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "color": "#FFEAA7", "description": "Friendships & social bonds"},
    "teen": {"icon": "🎭", "color": "#A855F7", "description": "Parent-teenager dynamics"}
}

EMOTIONAL_STATES = {
    "calm": {"icon": "😌", "color": "#10B981"},
    "frustrated": {"icon": "😤", "color": "#F59E0B"},
    "hurt": {"icon": "💔", "color": "#EF4444"},
    "anxious": {"icon": "😰", "color": "#8B5CF6"},
    "angry": {"icon": "😡", "color": "#DC2626"},
    "confused": {"icon": "😕", "color": "#6B7280"},
    "hopeful": {"icon": "🌅", "color": "#06B6D4"},
    "overwhelmed": {"icon": "🌀", "color": "#F97316"}
}

REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize Supabase - Enhanced error handling
@st.cache_resource
def init_supabase():
    try:
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {e}")
        return None

supabase = init_supabase()

# Enhanced Mobile-First WhatsApp-Inspired CSS
def inject_mobile_css():
    st.markdown("""
    <style>
    /* Global mobile-first design */
    .main > div {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* WhatsApp-style header */
    .chat-header {
        background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        color: white;
        padding: 1.2rem 1rem;
        text-align: center;
        position: sticky;
        top: 0;
        z-index: 100;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .chat-header h2 {
        margin: 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* Enhanced contact list */
    .contact-list {
        background: #f8f9fa;
        min-height: calc(100vh - 200px);
    }
    
    .contact-item {
        display: flex;
        align-items: center;
        padding: 1rem;
        background: white;
        border-bottom: 1px solid #E5E5E5;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .contact-item:hover {
        background: #f0f2f5;
        transform: translateX(2px);
    }
    
    .contact-item:active {
        background: #e4e6ea;
    }
    
    .contact-avatar {
        width: 55px;
        height: 55px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.6rem;
        margin-right: 1rem;
        flex-shrink: 0;
        position: relative;
        background: linear-gradient(135deg, var(--avatar-color, #25D366) 0%, var(--avatar-color-dark, #1da851) 100%);
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .contact-info {
        flex: 1;
        min-width: 0;
    }
    
    .contact-name {
        font-weight: 600;
        font-size: 1.1rem;
        color: #1f2937;
        margin: 0;
        line-height: 1.3;
    }
    
    .contact-last {
        color: #6b7280;
        font-size: 0.9rem;
        margin: 0.2rem 0 0 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }
    
    .contact-status {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    
    .contact-time {
        color: #9ca3af;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-indicator {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        margin-top: 0.3rem;
        box-shadow: 0 0 0 2px white;
    }
    
    .status-calm { background: linear-gradient(135deg, #10b981, #059669); }
    .status-tense { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .status-crisis { background: linear-gradient(135deg, #ef4444, #dc2626); }
    
    /* Enhanced conversation screen */
    .conversation-header {
        background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        color: white;
        padding: 1rem;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .back-button {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        font-size: 1.3rem;
        margin-right: 1rem;
        cursor: pointer;
        padding: 0.8rem;
        border-radius: 50%;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .back-button:hover {
        background: rgba(255,255,255,0.3);
    }
    
    /* Enhanced message input */
    .message-input-container {
        background: white;
        padding: 1rem;
        border-top: 1px solid #e5e7eb;
        position: sticky;
        bottom: 0;
        z-index: 50;
    }
    
    /* Enhanced AI intervention */
    .ai-intervention {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem;
        animation: slideIn 0.4s ease-out;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .ai-intervention h4 {
        margin: 0 0 0.8rem 0;
        font-size: 1.1rem;
    }
    
    .ai-intervention p {
        margin: 0.5rem 0;
        line-height: 1.5;
    }
    
    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateY(20px) scale(0.95); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0) scale(1); 
        }
    }
    
    /* Enhanced buttons */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        border-radius: 25px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Floating action button */
    .fab {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #25D366, #1da851);
        color: white;
        border: none;
        font-size: 1.8rem;
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4);
        z-index: 1000;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .fab:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 25px rgba(37, 211, 102, 0.5);
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: #6b7280;
        background: white;
        margin: 1rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Emotional state selector */
    .emotional-selector {
        display: flex;
        gap: 0.5rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 12px;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    
    .emotion-chip {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    
    .emotion-chip.active {
        border-color: var(--emotion-color);
        background: var(--emotion-color);
        color: white;
    }
    
    .emotion-chip:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .contact-name { font-size: 1rem; }
        .contact-last { font-size: 0.85rem; max-width: 160px; }
        .contact-time { font-size: 0.75rem; }
        .fab { bottom: 80px; }
    }
    
    /* Hide Streamlit sidebar */
    .css-1d391kg, .css-18e3th9 {
        display: none;
    }
    
    /* Message history */
    .message-history {
        max-height: 400px;
        overflow-y: auto;
        background: #f8f9fa;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .message-entry {
        padding: 1rem;
        border-bottom: 1px solid #e5e7eb;
        background: white;
        margin: 0.5rem;
        border-radius: 8px;
    }
    
    .message-entry:last-child {
        border-bottom: none;
    }
    
    .message-meta {
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }
    
    .message-content {
        font-size: 0.9rem;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

inject_mobile_css()

# Enhanced data functions with better error handling
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_contacts_and_history():
    if not supabase:
        return {}
        
    try:
        # Load contacts
        contacts_response = supabase.table("contacts").select("*").execute()
        contacts_data = {c["name"]: {
            "context": c["context"],
            "history": [],
            "emotional_journey": [],
            "breakthrough_moments": [],
            "created_at": c.get("created_at", datetime.datetime.now().isoformat())
        } for c in contacts_response.data}
        
        # Load messages
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
        st.warning(f"⚠️ Could not load data: {e}")
        return {}

def save_contact(name, context):
    if not supabase:
        return False
        
    try:
        supabase.table("contacts").insert({
            "name": name,
            "context": context,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        st.cache_data.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
        return False

def save_message(contact, message_type, original, result, sentiment, emotional_state, model, healing_score=0):
    if not supabase:
        return False
        
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
            "emotional_state": emotional_state
        }
        
        supabase.table("messages").insert(insert_data).execute()
        st.cache_data.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Error saving message: {e}")
        return False

# Initialize Session State with better defaults
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets.get("openrouter", {}).get("api_key", ""),
        'contacts': {},
        'active_contact': None,
        'current_emotional_state': 'calm',
        'conversation_goal': '',
        'show_intervention': False,
        'user_input': '',
        'page': 'contacts',  # 'contacts' or 'conversation'
        'user_stats': {
            'total_conversations': 0, 
            'healing_moments': 0, 
            'emotional_growth': 0,
            'days_since_start': 0
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Load contacts if empty
    if not st.session_state.contacts:
        st.session_state.contacts = load_contacts_and_history()

initialize_session()

# Token validation (simplified)
def validate_token():
    if REQUIRE_TOKEN and not st.session_state.token_validated:
        st.markdown('''
        <div class="chat-header">
            <h2>🎙️ The Third Voice</h2>
            <p style="margin: 0; opacity: 0.9;">When both people are speaking from pain, someone must be the third voice.</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.warning("🔐 Access restricted. Enter beta token to continue.")
        token = st.text_input("Token:", type="password")
        if st.button("Validate"):
            if token.startswith("ttv-beta-"):
                st.session_state.token_validated = True
                st.success("✅ Welcome to your healing journey")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid token")
        st.stop()

validate_token()

# Enhanced Mobile Contact List
def render_contact_list():
    if st.session_state.page == 'conversation':
        return
        
    # Header with stats
    total_contacts = len(st.session_state.contacts)
    total_messages = sum(len(c['history']) for c in st.session_state.contacts.values())
    
    st.markdown(f"""
    <div class="chat-header">
        <h2>🎙️ The Third Voice</h2>
        <p style="margin: 0; opacity: 0.9; font-size: 0.9rem;">
            {total_contacts} contacts • {total_messages} healing conversations
        </p>
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
            
            # Enhanced status calculation
            recent_history = contact_data['history'][-5:] if contact_data['history'] else []
            healing_scores = [h.get('healing_score', 0) for h in recent_history]
            
            if not healing_scores:
                status_class = "status-calm"
                status_text = "Ready"
            elif len(healing_scores) >= 3 and sum(healing_scores[-3:]) / 3 > 7:
                status_class = "status-calm"
                status_text = "Thriving"
            elif any(score < 4 for score in healing_scores[-2:]):
                status_class = "status-crisis"
                status_text = "Needs care"
            else:
                status_class = "status-tense"
                status_text = "Growing"
            
            # Last activity preview
            if contact_data['history']:
                last_entry = contact_data['history'][-1]
                last_time = last_entry['time']
                if last_entry['type'] == 'translate':
                    last_preview = f"Understood: {last_entry['original'][:30]}..."
                else:
                    last_preview = f"Coached: {last_entry['original'][:30]}..."
            else:
                last_time = "New"
                last_preview = f"Start your healing journey with {contact_name}"
            
            # Contact item with click handler
            if st.button(
                f"_{contact_name}",  # Hidden label
                key=f"contact_{contact_name}",
                help=f"Open conversation with {contact_name}",
                use_container_width=True
            ):
                st.session_state.active_contact = contact_name
                st.session_state.page = 'conversation'
                st.rerun()
            
            # Custom contact display overlay
            st.markdown(f"""
            <div class="contact-item" style="margin-top: -60px; pointer-events: none;">
                <div class="contact-avatar" style="--avatar-color: {context_info['color']}; --avatar-color-dark: {context_info['color']}dd;">
                    {context_info['icon']}
                </div>
                <div class="contact-info">
                    <div class="contact-name">{contact_name}</div>
                    <div class="contact-last">{last_preview}</div>
                </div>
                <div class="contact-status">
                    <div class="contact-time">{last_time}</div>
                    <div class="status-indicator {status_class}"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Enhanced empty state
        st.markdown("""
        <div class="empty-state">
            <h3>💝 Welcome to Your Healing Journey</h3>
            <p>Transform difficult conversations into moments of deep connection and understanding.</p>
            <p><strong>Ready to begin?</strong> Add your first contact below.</p>
        </div>
        """, unsafe_allow_html=True)

# Enhanced Mobile Conversation Screen
def render_conversation():
    if st.session_state.page != 'conversation' or not st.session_state.active_contact:
        return
        
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {})
    context = contact_data.get('context', 'family')
    context_info = CONTEXTS.get(context, CONTEXTS['family'])
    
    # Enhanced conversation header
    st.markdown(f"""
    <div class="conversation-header">
        <div class="back-button" onclick="document.querySelector('[data-testid*=\\"back_btn\\"]').click();">
            ←
        </div>
        <div>
            <div style="font-weight: 600; font-size: 1.2rem;">
                {context_info['icon']} {contact_name}
            </div>
            <div style="font-size: 0.85rem; opacity: 0.9;">
                {context_info['description']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back", key="back_btn", help="Return to contacts"):
        st.session_state.page = 'contacts'
        st.session_state.active_contact = None
        st.rerun()
    
    # Emotional state selector
    st.markdown("**How are you feeling right now?**")
    
    cols = st.columns(4)
    for i, (state, info) in enumerate(EMOTIONAL_STATES.items()):
        with cols[i % 4]:
            is_active = st.session_state.current_emotional_state == state
            button_style = f"""
                background: {'linear-gradient(135deg, ' + info['color'] + ', ' + info['color'] + 'dd)' if is_active else 'white'};
                color: {'white' if is_active else info['color']};
                border: 2px solid {info['color']};
            """
            
            if st.button(
                f"{info['icon']}",
                key=f"emotion_{state}",
                help=state.title()
            ):
                st.session_state.current_emotional_state = state
                st.rerun()
    
    # Recent history (condensed)
    if contact_data.get('history'):
        st.markdown("**Recent conversations:**")
        with st.expander(f"📚 {len(contact_data['history'])} previous messages", expanded=False):
            recent = contact_data['history'][-3:]  # Show last 3
            for entry in reversed(recent):
                st.markdown(f"""
                <div class="message-entry">
                    <div class="message-meta">
                        {entry['time']} • {entry['type'].title()} • Score: {entry.get('healing_score', 0)}/10
                    </div>
                    <div class="message-content">
                        <strong>You:</strong> {entry['original'][:100]}{'...' if len(entry['original']) > 100 else ''}<br>
                        <strong>Guidance:</strong> {entry['result'][:150]}{'...' if len(entry['result']) > 150 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Enhanced message input
    st.markdown("### 💬 What's happening?")
    
    user_input = st.text_area(
        "",
        placeholder=f"Share what {contact_name} said, or what you want to say to them...",
        height=120,
        key="conversation_input",
        help="Paste their message or write your response"
    )
    
    # Smart AI intervention
    if user_input and len(user_input.strip()) > 15:
        crisis_indicators = [
            'hate', 'never again', 'done with', 'can\'t take', 'always does',
            'stupid', 'ridiculous', 'impossible', 'fed up', 'enough'
        ]
        paste_indicators = ['said:', 'wrote:', 'texted:', 'told me:', '\n\n']
        
        is_crisis = any(indicator in user_input.lower() for indicator in crisis_indicators)
        is_paste = any(indicator in user_input for indicator in paste_indicators)
        is_emotional = st.session_state.current_emotional_state in ['angry', 'frustrated', 'hurt', 'overwhelmed']
        
        if is_crisis or is_emotional:
            emotion_info = EMOTIONAL_STATES[st.session_state.current_emotional_state]
            st.markdown(f"""
            <div class="ai-intervention">
                <h4>{emotion_info['icon']} I can feel your {st.session_state.current_emotional_state} energy</h4>
                <p>Before we respond to {contact_name}, let's remember: they're probably hurting too.</p>
                <p>💝 <strong>What they might really need:</strong> To feel heard, understood, valued</p>
                <p>🌟 <strong>What healing looks like:</strong> Responding from love, not pain</p>
                <p><em>Take a breath. Let's find the words that build bridges.</em></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button(
            "✨ Transform This Message", 
            use_container_width=True, 
            disabled=not user_input.strip(),
            help="Get AI guidance for healing communication"
        ):
            process_message_enhanced(contact_name, user_input, context)
    
    with col2:
        if st.button("🗑️", help="Clear input"):
            st.session_state.conversation_input = ''
            st.rerun()

# Enhanced AI processing with better prompts
def process_message_enhanced(contact_name, message, context):
    if not message.strip():
        return
        
    current_emotion = st.session_state.current_emotional_state
    emotion_context = EMOTIONAL_STATES[current_emotion]
    
    with st.spinner(f"{emotion_context['icon']} Channeling wisdom and compassion..."):
        # Determine mode and create specialized prompt
        paste_indicators = ['said:', 'wrote:', 'texted:', 'told me:', '\n']
        is_incoming = any(indicator in message.lower() for indicator in paste_indicators)
        
        if is_incoming:
            mode = "translate"
            system_prompt = f"""You are The Third Voice - a wise, compassionate relationship guide. 

The user is feeling {current_emotion} about something {contact_name} said in their {context} relationship.

Your role:
1. Help them understand what {contact_name} might REALLY mean behind their words
2. Identify the deeper need or pain driving the communication
3. Suggest how to respond with both boundaries AND love
4. Keep it concise but deeply insightful (2-3 paragraphs max)

Remember: Both people are usually speaking from pain. Help find the healing path."""
        else:
            mode = "coach"
            system_prompt = f"""You are The Third Voice - a wise relationship coach helping someone communicate more effectively.

The user wants to say something to {contact_name} in their {context} relationship, and they're feeling {current_emotion}.

Your role:
1. Help them express their truth with love and respect
2. Reframe reactive language into connecting language
3. Suggest words that invite dialog rather than defensiveness
4. Keep it practical and immediately usable (2-3 paragraphs max)

Focus on: What would love say here? How can this build the relationship?"""
        
        # Try multiple AI models for reliability
        models = [
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free"
        ]
        
        success = False
        for model in models:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                
                response = requests.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                    json={
                        "model": model, 
                        "messages": messages, 
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                reply = response.json()["choices"][0]["message"]["content"].strip()
                
                # Enhanced result display
                emotion_info = EMOTIONAL_STATES[current_emotion]
                st.markdown(f"""
                <div class="ai-intervention">
                    <h4>🌟 Your Third Voice Guidance</h4>
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        {reply}
                    </div>
                    <p style="font-size: 0.9rem; opacity: 0.9; margin: 0.5rem 0 0 0;">
                        <em>From {current_emotion} to healing • {contact_name} • {context.title()} relationship</em>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Calculate healing score based on multiple factors
                healing_score = calculate_healing_score(reply, current_emotion, mode)
                
                # Save to history
                new_entry = {
                    "id": f"{mode}_{datetime.datetime.now().timestamp()}",
                    "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                    "type": mode,
                    "original": message,
                    "result": reply,
                    "sentiment": "healing",
                    "emotional_state": current_emotion,
                    "model": model.split('/')[-1],
                    "healing_score": healing_score
                }
                
                # Update session state
                if contact_name in st.session_state.contacts:
                    st.session_state.contacts[contact_name]['history'].append(new_entry)
                
                # Save to database
                save_message(
                    contact_name, mode, message, reply, 
                    "healing", current_emotion, model, healing_score
                )
                
                # Celebration for breakthroughs
                if healing_score >= 8:
                    st.success("🌟 This feels like a breakthrough moment!")
                    st.balloons()
                elif healing_score >= 6:
                    st.info("💝 Beautiful progress in your healing journey")
                
                success = True
                break
                
            except requests.exceptions.Timeout:
                st.warning(f"⏱️ {model} is taking too long, trying next...")
                continue
            except requests.exceptions.RequestException as e:
                if "rate limit" in str(e).lower():
                    st.warning(f"⏳ {model} is busy, trying next...")
                    continue
                else:
                    continue
            except Exception as e:
                continue
        
        if not success:
            st.error("🔄 All AI services are temporarily unavailable. Please try again in a few moments.")

def calculate_healing_score(reply, emotion, mode):
    """Calculate healing potential score based on response quality"""
    score = 5  # Base score
    
    # Length and depth indicators
    if len(reply) > 200:
        score += 1
    if len(reply.split('.')) >= 3:  # Multiple sentences
        score += 1
    
    # Positive language indicators
    positive_words = [
        'understand', 'love', 'connect', 'healing', 'growth', 'compassion',
        'listen', 'empathy', 'bridge', 'together', 'support', 'care'
    ]
    score += min(2, sum(1 for word in positive_words if word in reply.lower()))
    
    # Emotional intelligence indicators
    if any(phrase in reply.lower() for phrase in [
        'they might be feeling', 'what they really need', 'behind their words',
        'deeper need', 'speaking from', 'try saying'
    ]):
        score += 1
    
    # Bonus for addressing difficult emotions
    if emotion in ['angry', 'hurt', 'frustrated', 'overwhelmed'] and score >= 7:
        score += 1
    
    return min(10, score)

# Enhanced Quick Add Contact
def render_quick_add():
    if st.session_state.page == 'conversation':
        return
        
    # Floating add button
    st.markdown("""
    <div class="fab" onclick="document.querySelector('[data-testid*=\\"add_contact_btn\\"]').click();">
        ➕
    </div>
    """, unsafe_allow_html=True)
    
    # Add contact expander
    with st.expander("➕ Add New Contact", expanded=False):
        st.markdown("**Who would you like to heal conversations with?**")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            new_name = st.text_input(
                "Name", 
                placeholder="Sarah, Mom, Dad, Alex...", 
                key="new_contact_name"
            )
        with col2:
            new_context = st.selectbox(
                "Relationship", 
                list(CONTEXTS.keys()), 
                key="new_contact_context",
                format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}"
            )
        
        # Context preview
        if new_context:
            context_info = CONTEXTS[new_context]
            st.markdown(f"""
            <div style="background: {context_info['color']}20; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                {context_info['icon']} <strong>{context_info['description']}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("✨ Start Healing Journey", key="add_contact_btn", use_container_width=True):
            if new_name.strip():
                if save_contact(new_name.strip(), new_context):
                    # Update session state immediately
                    st.session_state.contacts[new_name.strip()] = {
                        "context": new_context,
                        "history": [],
                        "emotional_journey": [],
                        "breakthrough_moments": [],
                        "created_at": datetime.datetime.now().isoformat()
                    }
                    st.success(f"✨ Added {new_name.strip()} to your healing circle")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Please enter a name")

# Navigation and stats
def render_stats_sidebar():
    """Optional stats panel for insights"""
    if st.sidebar.checkbox("📊 Healing Insights", value=False):
        if st.session_state.contacts:
            total_messages = sum(len(c['history']) for c in st.session_state.contacts.values())
            avg_healing_score = 0
            total_scores = []
            
            for contact_data in st.session_state.contacts.values():
                scores = [h.get('healing_score', 0) for h in contact_data['history']]
                total_scores.extend(scores)
            
            if total_scores:
                avg_healing_score = sum(total_scores) / len(total_scores)
            
            st.sidebar.markdown(f"""
            **🌟 Your Healing Journey**
            - **Contacts:** {len(st.session_state.contacts)}
            - **Conversations:** {total_messages}
            - **Avg Healing Score:** {avg_healing_score:.1f}/10
            - **Current Mood:** {EMOTIONAL_STATES[st.session_state.current_emotional_state]['icon']} {st.session_state.current_emotional_state.title()}
            """)
            
            # Emotional journey chart
            if total_scores:
                import plotly.graph_objects as go
                fig = go.Figure(data=go.Scatter(y=total_scores[-20:], mode='lines+markers'))
                fig.update_layout(
                    title="Recent Healing Progress",
                    height=300,
                    showlegend=False
                )
                st.sidebar.plotly_chart(fig, use_container_width=True)

# Main App Flow
def main():
    """Main application controller"""
    
    # Always render the appropriate screen based on state
    if st.session_state.page == 'contacts':
        render_contact_list()
        render_quick_add()
    elif st.session_state.page == 'conversation':
        render_conversation()
    
    # Optional stats in sidebar
    render_stats_sidebar()
    
    # Debug info (remove in production)
    if st.sidebar.checkbox("🔧 Debug Info", value=False):
        st.sidebar.json({
            "page": st.session_state.page,
            "active_contact": st.session_state.active_contact,
            "emotional_state": st.session_state.current_emotional_state,
            "contacts_count": len(st.session_state.contacts),
            "supabase_connected": supabase is not None
        })

# Run the app
if __name__ == "__main__":
    main()
