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
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
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
            "context": c["context"], 
            "history": [], 
            "created_at": c.get("created_at", datetime.datetime.now().isoformat()),
            "id": c.get("id")
        } for c in supabase.table("contacts").select("*").execute().data}
        
        messages = supabase.table("messages").select("*").order("timestamp").execute().data
        for msg in messages:
            contact_name = msg["contact_name"]
            if contact_name not in contacts_data:
                contacts_data[contact_name] = {
                    "context": "family", 
                    "history": [], 
                    "created_at": datetime.datetime.now().isoformat(),
                    "id": None
                }
            contacts_data[contact_name]["history"].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"], 
                "original": msg["original"], 
                "result": msg["result"],
                "healing_score": msg.get("healing_score", 0)
            })
        return contacts_data
    except Exception as e:
        st.warning(f"Could not load data: {e}")
        return {}

# Save data
def save_contact(name, context, contact_id=None):
    if not supabase or not name.strip():
        return False
    try:
        contact_data = {"name": name, "context": context}
        if contact_id:
            supabase.table("contacts").update(contact_data).eq("id", contact_id).execute()
        else:
            contact_data["created_at"] = datetime.datetime.now().isoformat()
            supabase.table("contacts").insert(contact_data).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
        return False

def delete_contact(contact_id):
    if not supabase or not contact_id:
        return False
    try:
        contact_name = supabase.table("contacts").select("name").eq("id", contact_id).execute().data[0]["name"]
        supabase.table("messages").delete().eq("contact_name", contact_name).execute()
        supabase.table("contacts").delete().eq("id", contact_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error deleting contact: {e}")
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
        "user_input": "",
        "clear_input": False,
        "edit_contact": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

# Process message
def process_message(contact_name, message, context):
    if not message.strip():
        return
    
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    
    system_prompt = (
        f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}. "
        f"{'Understand what they mean and suggest a loving response.' if is_incoming else 'Reframe their message to be constructive and loving.'} "
        "Keep it concise, insightful, and actionable (2-3 paragraphs)."
    )
    
    with st.spinner("🤖 Processing..."):
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
            healing_score = min(10, healing_score)
            
            new_message = {
                "id": f"{mode}_{datetime.datetime.now().timestamp()}", 
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": mode, 
                "original": message, 
                "result": response, 
                "healing_score": healing_score
            }
            
            if contact_name not in st.session_state.contacts:
                st.session_state.contacts[contact_name] = {
                    "context": "family", 
                    "history": [], 
                    "created_at": datetime.datetime.now().isoformat(),
                    "id": None
                }
            
            st.session_state.contacts[contact_name]["history"].append(new_message)
            save_message(contact_name, mode, message, response, "calm", healing_score)
            st.session_state[f"last_response_{contact_name}"] = {
                "response": response,
                "healing_score": healing_score,
                "timestamp": datetime.datetime.now().timestamp(),
                "model": MODEL
            }
            st.session_state.clear_input = True
                
        except Exception as e:
            st.error(f"Failed to process message: {e}")

# First time user screen
def render_first_time_screen():
    st.markdown("### 🎙️ Welcome to The Third Voice")
    st.markdown("Choose a relationship type to get started, or add a custom contact:")
    
    cols = st.columns(2)
    contexts = list(CONTEXTS.items())
    
    for i, (context_key, context_info) in enumerate(contexts):
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
                    st.session_state.contacts[contact_name] = {
                        "context": context_key, 
                        "history": [], 
                        "created_at": datetime.datetime.now().isoformat(),
                        "id": None
                    }
                    st.session_state.active_contact = contact_name
                    st.session_state.page = "conversation"
                    st.rerun()
    
    st.markdown("---")
    
    with st.form("add_custom_contact"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}")
        
        if st.form_submit_button("Add Custom Contact"):
            if name.strip() and save_contact(name, context):
                st.session_state.contacts[name] = {
                    "context": context, 
                    "history": [], 
                    "created_at": datetime.datetime.now().isoformat(),
                    "id": None
                }
                st.session_state.active_contact = name
                st.session_state.page = "conversation"
                st.rerun()

# Contact list (simplified without edit/delete buttons)
def render_contact_list():
    if st.session_state.page != "contacts":
        return
        
    st.markdown("### 🎙️ The Third Voice")
    
    for name, data in sorted(st.session_state.contacts.items(), 
                           key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"], 
                           reverse=True):
        context = CONTEXTS.get(data["context"], CONTEXTS["family"])
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:30]}..." if last_msg else "Start chatting!"
        time = last_msg["time"] if last_msg else "New"
        
        if st.button(
            f"**{context['icon']} {name}**  \n"
            f"{context['description']} • {time}  \n"
            f"`{preview}`",
            key=f"contact_{name}",
            use_container_width=True
        ):
            st.session_state.active_contact = name
            st.session_state.page = "conversation"
            st.rerun()
        
        st.markdown("---")
    
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.page = "add_contact"
        st.rerun()

# Edit contact page with delete option
def render_edit_contact():
    if st.session_state.page != "edit_contact" or not st.session_state.edit_contact:
        return
        
    contact = st.session_state.edit_contact
    st.markdown(f"### ✏️ Edit Contact: {contact['name']}")
    
    if st.button("← Back", key="back_to_conversation", use_container_width=True):
        st.session_state.page = "conversation"
        st.session_state.edit_contact = None
        st.rerun()
    
    with st.form("edit_contact_form"):
        name = st.text_input("Name", value=contact["name"], placeholder="Sarah, Mom, Dad...")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), 
                             index=list(CONTEXTS.keys()).index(contact["context"]),
                             format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                if name.strip() and save_contact(name, context, contact["id"]):
                    st.success(f"Updated {name}")
                    st.session_state.page = "conversation"
                    st.session_state.edit_contact = None
                    st.rerun()
        
        with col2:
            if st.form_submit_button("🗑️ Delete Contact"):
                if delete_contact(contact["id"]):
                    st.success(f"Deleted contact: {name}")
                    st.session_state.page = "contacts"
                    st.session_state.edit_contact = None
                    st.rerun()

# Conversation screen with edit button
def render_conversation():
    if st.session_state.page != "conversation" or not st.session_state.active_contact:
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    
    back_col, edit_col, _ = st.columns([2, 2, 6])
    
    with back_col:
        if st.button("← Back", key="back_btn", use_container_width=True):
            st.session_state.page = "contacts"
            st.session_state.active_contact = None
            st.rerun()
    
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            st.session_state.page = "edit_contact"
            st.rerun()
    
    st.markdown("---")
    st.markdown("#### 💭 Your Input")
    input_value = "" if st.session_state.get("clear_input", False) else st.session_state.get("conversation_input_value", "")
    
    user_input = st.text_area(
        "What's happening?", 
        value=input_value,
        key="conversation_input", 
        placeholder="Share their message or your response...", 
        height=120
    )
    
    if st.session_state.get("clear_input", False):
        st.session_state.clear_input = False
        st.session_state.conversation_input_value = ""
    else:
        st.session_state.conversation_input_value = user_input
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", 
                    disabled=not user_input.strip(), use_container_width=True):
            last_response_key = f"last_response_{contact_name}"
            if last_response_key in st.session_state:
                del st.session_state[last_response_key]
            process_message(contact_name, user_input, context)
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.clear_input = True
            st.rerun()
    
    st.markdown("---")
    st.markdown("#### 🤖 AI Response")
    
    last_response_key = f"last_response_{contact_name}"
    if last_response_key in st.session_state:
        last_resp = st.session_state[last_response_key]
        if datetime.datetime.now().timestamp() - last_resp["timestamp"] < 60:
            with st.container():
                st.markdown("**AI Guidance:**")
                st.text_area(
                    "", 
                    value=last_resp['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False
                )
                
                col_score, col_model = st.columns([1, 1])
                with col_score:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Healing Score: {last_resp['healing_score']}/10")
                    else:
                        st.info(f"💡 Healing Score: {last_resp['healing_score']}/10")
                
                with col_model:
                    st.caption(f"🤖 Model: {last_resp.get('model', MODEL)}")
                
                if last_resp["healing_score"] >= 8:
                    st.balloons()
        else:
            st.info("💭 Your AI response will appear here after you click Transform")
    else:
        st.info("💭 Your AI response will appear here after you click Transform")
    
    st.markdown("---")
    st.markdown("#### 📜 Conversation History")
    
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total)")
        
        with st.expander("View Chat History", expanded=False):
            for msg in reversed(history[-10:]):
                st.markdown(f"""
                **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                """)
                
                with st.container():
                    st.markdown("**Your Message:**")
                    st.info(msg['original'])
                
                with st.container():
                    st.markdown("**AI Guidance:**")
                    st.text_area(
                        "",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg['id']}",
                        disabled=False
                    )
                
                st.markdown("---")
    else:
        st.info("📝 No chat history yet. Start a conversation above!")

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
                    "created_at": datetime.datetime.now().isoformat(),
                    "id": None
                }
                st.success(f"Added {name}")
                st.session_state.page = "contacts"
                st.rerun()

# Main app
def main():
    st.set_page_config(page_title="The Third Voice", layout="wide")
    initialize_session()
    
    if not st.session_state.contacts:
        render_first_time_screen()
    else:
        if st.session_state.page == "edit_contact":
            render_edit_contact()
        else:
            render_contact_list()
    
    render_conversation()
    render_add_contact()

if __name__ == "__main__":
    main()
