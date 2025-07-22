import streamlit as st
import datetime
import requests
from supabase import create_client

# Constants
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"},
    "teen": {"icon": "🎭", "description": "Parent-teenager dynamics"}
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

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-2-9b-it:free"

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    except Exception as e:
        st.error(f"Supabase initialization failed: {e}")
        return None

supabase = init_supabase()

# Load data
@st.cache_data(ttl=60)
def load_contacts_and_history():
    if not supabase:
        return {}
    try:
        contacts_data = {c["name"]: {
            "context": c["context"], "history": [], "created_at": c.get("created_at", datetime.datetime.now().isoformat())
        } for c in supabase.table("contacts").select("*").execute().data}
        
        for msg in supabase.table("messages").select("*").order("timestamp").execute().data:
            contact_name = msg["contact_name"]
            if contact_name not in contacts_data:
                contacts_data[contact_name] = {"context": "family", "history": [], "created_at": datetime.datetime.now().isoformat()}
            contacts_data[contact_name]["history"].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "emotional_state": msg.get("emotional_state", "calm"),
                "healing_score": msg.get("healing_score", 0)
            })
        return contacts_data
    except Exception as e:
        st.warning(f"Could not load data: {e}")
        return {}

# Save data
def save_contact(name, context):
    if not supabase or not name.strip():
        return False
    try:
        supabase.table("contacts").insert({
            "name": name, "context": context, "created_at": datetime.datetime.now().isoformat()
        }).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
        return False

def save_message(contact, message_type, original, result, emotional_state, healing_score):
    if not supabase:
        return False
    try:
        supabase.table("messages").insert({
            "contact_name": contact, "type": message_type, "original": original, "result": result,
            "emotional_state": emotional_state, "healing_score": healing_score,
            "timestamp": datetime.datetime.now().isoformat()
        }).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving message: {e}")
        return False

# Initialize session state
def initialize_session():
    defaults = {
        "contacts": load_contacts_and_history(),
        "page": "contacts",
        "active_contact": None,
        "current_emotional_state": "calm",
        "user_input": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

# Process message with AI
def process_message(contact_name, message, context):
    if not message.strip():
        return
    current_emotion = st.session_state.current_emotional_state
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    
    system_prompt = (
        f"You are a compassionate relationship guide. The user is feeling {current_emotion} in their {context} relationship with {contact_name}. "
        f"{'Understand what they mean and suggest a loving response.' if is_incoming else 'Reframe their message to be constructive and loving.'} "
        "Keep it concise, insightful, and actionable (2-3 paragraphs)."
    )
    
    with st.spinner(f"{EMOTIONAL_STATES[current_emotion]['icon']} Processing..."):
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {st.secrets.get('openrouter', {}).get('api_key', '')}"},
                json={"model": MODEL, "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ], "temperature": 0.7, "max_tokens": 500},
                timeout=15
            ).json()["choices"][0]["message"]["content"].strip()
            
            healing_score = 5 + (1 if len(response) > 200 else 0) + (
                min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in response.lower()))
            )
            healing_score = min(10, healing_score + (1 if current_emotion in ["angry", "hurt", "frustrated"] else 0))
            
            st.session_state.contacts[contact_name]["history"].append({
                "id": f"{mode}_{datetime.datetime.now().timestamp()}",
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": mode,
                "original": message,
                "result": response,
                "emotional_state": current_emotion,
                "healing_score": healing_score
            })
            save_message(contact_name, mode, message, response, current_emotion, healing_score)
            
            st.success(f"🌟 Guidance:\n{response}")
            if healing_score >= 8:
                st.balloons()
        except Exception as e:
            st.error(f"Failed to process message: {e}")

# Contact list
def render_contact_list():
    if st.session_state.page != "contacts":
        return
    st.markdown(f"### 🎙️ The Third Voice ({len(st.session_state.contacts)} contacts)")
    
    if not st.session_state.contacts:
        st.info("No contacts yet. Add one to start your healing journey!")
    else:
        for name

, data in sorted(st.session_state.contacts.items(), key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"], reverse=True):
            context = CONTEXTS.get(data["context"], CONTEXTS["family"])
            last_msg = data["history"][-1] if data["history"] else None
            preview = f"{last_msg['original'][:30]}..." if last_msg else "Start chatting!"
            time = last_msg["time"] if last_msg else "New"
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{context['icon']} **{name}** - {context['description']}\n\n{preview}")
                with col2:
                    st.write(time)
                if st.button("Chat", key=f"contact_{name}"):
                    st.session_state.active_contact = name
                    st.session_state.page = "conversation"
                    st.rerun()

# Conversation screen
def render_conversation():
    if st.session_state.page != "conversation" or not st.session_state.active_contact:
        return
    contact_name = st.session_state.active_contact
    context = st.session_state.contacts[contact_name]["context"]
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    if st.button("← Back", key="back_btn"):
        st.session_state.page = "contacts"
        st.session_state.active_contact = None
        st.rerun()
    
    st.write("**How are you feeling?**")
    cols = st.columns(4)
    for i, (state, info) in enumerate(EMOTIONAL_STATES.items()):
        with cols[i % 4]:
            if st.button(f"{info['icon']} {state.title()}", key=f"emotion_{state}", use_container_width=True):
                st.session_state.current_emotional_state = state
                st.rerun()
    
    if st.session_state.contacts[contact_name]["history"]:
        with st.expander("Recent Messages", expanded=False):
            for msg in reversed(st.session_state.contacts[contact_name]["history"][-3:]):
                st.markdown(f"**{msg['time']} ({msg['type'].title()})** - Score: {msg['healing_score']}/10\n\n**You**: {msg['original'][:100]}...\n**Guidance**: {msg['result'][:150]}...")
    
    user_input = st.text_area("What's happening?", key="conversation_input", placeholder="Share their message or your response...")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", disabled=not user_input.strip()):
            process_message(contact_name, user_input, context)
    with col2:
        if st.button("🗑️ Clear", key="clear_input"):
            st.session_state.conversation_input = ""

# Add contact
def render_add_contact():
    if st.session_state.page != "contacts":
        return
    with st.form("add_contact_form"):
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}")
        if st.form_submit_button("Add Contact"):
            if name.strip() and save_contact(name, context):
                st.session_state.contacts[name] = {
                    "context": context, "history": [], "created_at": datetime.datetime.now().isoformat()
                }
                st.success(f"Added {name}")
                st.rerun()

# Main app
def main():
    st.set_page_config(page_title="The Third Voice", layout="wide")
    initialize_session()
    render_contact_list()
    render_conversation()
    render_add_contact()

if __name__ == "__main__":
    main()
