import streamlit as st
import datetime
import requests
from supabase import create_client

# Constants (removed teen category)
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
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
        
        # Load messages and group by contact
        messages = supabase.table("messages").select("*").order("timestamp").execute().data
        for msg in messages:
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
        supabase.table("contacts").insert({"name": name, "context": context, "created_at": datetime.datetime.now().isoformat()}).execute()
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
            "emotional_state": emotional_state, "healing_score": healing_score, "timestamp": datetime.datetime.now().isoformat()
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

# Process message
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
                json={
                    "model": MODEL, 
                    "messages": [
                        {"role": "system", "content": system_prompt}, 
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7, 
                    "max_tokens": 500
                }, 
                timeout=15
            ).json()["choices"][0]["message"]["content"].strip()
            
            healing_score = 5 + (1 if len(response) > 200 else 0) + min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in response.lower()))
            healing_score = min(10, healing_score + (1 if current_emotion in ["angry", "hurt", "frustrated"] else 0))
            
            # Add to session state history immediately
            new_message = {
                "id": f"{mode}_{datetime.datetime.now().timestamp()}", 
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": mode, 
                "original": message, 
                "result": response, 
                "emotional_state": current_emotion, 
                "healing_score": healing_score
            }
            
            if contact_name not in st.session_state.contacts:
                st.session_state.contacts[contact_name] = {"context": "family", "history": [], "created_at": datetime.datetime.now().isoformat()}
            
            st.session_state.contacts[contact_name]["history"].append(new_message)
            
            # Save to database
            save_message(contact_name, mode, message, response, current_emotion, healing_score)
            
            # Create a persistent container for the AI response
            response_container = st.container()
            with response_container:
                st.success(f"🌟 **AI Guidance:**\n\n{response}")
                if healing_score >= 8:
                    st.balloons()
                    
            # Store the response in session state to persist across reruns
            st.session_state[f"last_response_{contact_name}"] = {
                "response": response,
                "healing_score": healing_score,
                "timestamp": datetime.datetime.now().timestamp()
            }
                
        except Exception as e:
            st.error(f"Failed to process message: {e}")

# First time user screen - context buttons as default contacts
def render_first_time_screen():
    st.markdown("### 🎙️ Welcome to The Third Voice")
    st.markdown("Choose a relationship type to get started, or add a custom contact:")
    
    # Context buttons as starter contacts
    cols = st.columns(2)
    contexts = list(CONTEXTS.items())
    
    for i, (context_key, context_info) in enumerate(contexts):
        with cols[i % 2]:
            if st.button(
                f"{context_info['icon']} {context_key.title()}\n{context_info['description']}", 
                key=f"context_{context_key}",
                use_container_width=True
            ):
                # Create a default contact name based on context
                default_names = {
                    "romantic": "Partner",
                    "coparenting": "Co-parent",
                    "workplace": "Colleague", 
                    "family": "Family Member",
                    "friend": "Friend"
                }
                contact_name = default_names.get(context_key, context_key.title())
                
                # Save and activate this contact
                if save_contact(contact_name, context_key):
                    st.session_state.contacts[contact_name] = {
                        "context": context_key, 
                        "history": [], 
                        "created_at": datetime.datetime.now().isoformat()
                    }
                    st.session_state.active_contact = contact_name
                    st.session_state.page = "conversation"
                    st.rerun()
    
    st.markdown("---")
    
    # Add custom contact option
    with st.form("add_custom_contact"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}")
        
        if st.form_submit_button("Add Custom Contact"):
            if name.strip() and save_contact(name, context):
                st.session_state.contacts[name] = {
                    "context": context, 
                    "history": [], 
                    "created_at": datetime.datetime.now().isoformat()
                }
                st.session_state.active_contact = name
                st.session_state.page = "conversation"
                st.rerun()

# Contact list for existing users
def render_contact_list():
    if st.session_state.page != "contacts":
        return
        
    st.markdown("### 🎙️ The Third Voice")
    
    # Show existing contacts - merge name with button
    for name, data in sorted(st.session_state.contacts.items(), key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"], reverse=True):
        context = CONTEXTS.get(data["context"], CONTEXTS["family"])
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:30]}..." if last_msg else "Start chatting!"
        time = last_msg["time"] if last_msg else "New"
        
        # Merge contact info into the button itself
        button_text = f"{context['icon']} {name}\n{context['description']} • {time}\n{preview}"
        
        if st.button(button_text, key=f"contact_{name}", use_container_width=True):
            st.session_state.active_contact = name
            st.session_state.page = "conversation"
            st.rerun()
    
    # Add new contact button
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.page = "add_contact"
        st.rerun()

# Conversation screen (simplified - removed emotional state selection)
def render_conversation():
    if st.session_state.page != "conversation" or not st.session_state.active_contact:
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": []})
    context = contact_data["context"]
    history = contact_data["history"]
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    
    if st.button("← Back", key="back_btn", use_container_width=True):
        st.session_state.page = "contacts"
        st.session_state.active_contact = None
        st.rerun()
    
    # Show chat history
    st.markdown("---")
    if history:
        st.markdown(f"**Chat History** ({len(history)} messages)")
        with st.expander("Recent Messages", expanded=True):
            for msg in reversed(history[-10:]):  # Show last 10 messages
                emotion_info = EMOTIONAL_STATES.get(msg['emotional_state'], EMOTIONAL_STATES['calm'])
                
                st.markdown(f"""
                **{msg['time']}** | {emotion_info['icon']} {msg['emotional_state'].title()} | 
                **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                
                **Your Message:**
                > {msg['original']}  
                
                **AI Guidance:**
                > {msg['result']}
                """)
                st.markdown("---")
    else:
        st.info("No chat history yet. Start a conversation below!")
    
    # Show last AI response if it exists (to prevent disappearing)
    last_response_key = f"last_response_{contact_name}"
    if last_response_key in st.session_state:
        last_resp = st.session_state[last_response_key]
        # Only show if it's recent (within last 30 seconds to avoid stale responses)
        if datetime.datetime.now().timestamp() - last_resp["timestamp"] < 30:
            with st.container():
                st.success(f"🌟 **AI Guidance:**\n\n{last_resp['response']}")
                if last_resp["healing_score"] >= 8:
                    st.info("✨ High healing score achieved!")
    
    # Input area (removed emotional state selection for less friction)
    user_input = st.text_area(
        "What's happening?", 
        key="conversation_input", 
        placeholder="Share their message or your response...", 
        height=120
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", 
                    disabled=not user_input.strip(), use_container_width=True):
            # Clear the previous response before processing new one
            last_response_key = f"last_response_{contact_name}"
            if last_response_key in st.session_state:
                del st.session_state[last_response_key]
            
            process_message(contact_name, user_input, context)
            # Clear input after processing
            st.session_state.conversation_input = ""
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", key="clear_input", use_container_width=True):
            st.session_state.conversation_input = ""
            st.rerun()

# Add contact page
def render_add_contact():
    if st.session_state.page != "add_contact":
        return
        
    st.markdown("### ➕ Add New Contact")
    
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        st.session_state.page = "contacts"
        st.rerun()
    
    with st.form("add_contact_form"):
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), 
                              format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}")
        
        if st.form_submit_button("Add Contact"):
            if name.strip() and save_contact(name, context):
                st.session_state.contacts[name] = {
                    "context": context, 
                    "history": [], 
                    "created_at": datetime.datetime.now().isoformat()
                }
                st.success(f"Added {name}")
                st.session_state.page = "contacts"
                st.rerun()

# Main app
def main():
    st.set_page_config(page_title="The Third Voice", layout="wide")
    initialize_session()
    
    # Show first time screen if no contacts, otherwise show contact list
    if not st.session_state.contacts:
        render_first_time_screen()
    else:
        render_contact_list()
    
    render_conversation()
    render_add_contact()

if __name__ == "__main__":
    main()
