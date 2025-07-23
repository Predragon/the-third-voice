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
MODEL = "google/gemma-2-9b-it:free" # Your model name

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
                    "context": "family", # Default context if message exists but contact doesn't
                    "history": [],
                    "created_at": datetime.datetime.now().isoformat(),
                    "id": None # Will need to be updated if contact is later saved
                }
            contacts_data[contact_name]["history"].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "healing_score": msg.get("healing_score", 0),
                "model": msg.get("model", "Unknown")
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
        # Get contact name before deleting contact, to delete associated messages
        contact_name_data = supabase.table("contacts").select("name").eq("id", contact_id).execute().data
        if contact_name_data:
            contact_name = contact_name_data[0]["name"]
            supabase.table("messages").delete().eq("contact_name", contact_name).execute()

        supabase.table("contacts").delete().eq("id", contact_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error deleting contact: {e}")
        return False

def save_message(contact, message_type, original, result, emotional_state, healing_score, model_used):
    if not supabase:
        return False
    try:
        supabase.table("messages").insert({
            "contact_name": contact, "type": message_type, "original": original, "result": result,
            "emotional_state": emotional_state, "healing_score": healing_score,
            "timestamp": datetime.datetime.now().isoformat(), "model": model_used
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
        "edit_contact": None,
        "conversation_input_text": "",
        "edit_contact_name_input": "",
        "add_contact_name_input": "",
        "add_contact_context_select": list(CONTEXTS.keys())[0],
        "last_error_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

# Process message
def process_message(contact_name, message, context):
    st.session_state.last_error_message = None

    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty. Please type something to transform."
        return

    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"

    system_prompt = (
        f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}. "
        f"{'Understand what they mean and suggest a loving response.' if is_incoming else 'Reframe their message to be constructive and loving.'} "
        "Keep it concise, insightful, and actionable (2-3 paragraphs)."
    )

    try:
        with st.spinner("🤖 Processing..."):
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
                timeout=25
            ).json()["choices"][0]["message"]["content"].strip()

        healing_score = 5 + (1 if len(response) > 200 else 0) + min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in response.lower()))
        healing_score = min(10, healing_score)

        new_message = {
            "id": f"{mode}_{datetime.datetime.now().timestamp()}",
            "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
            "type": mode,
            "original": message,
            "result": response,
            "healing_score": healing_score,
            "model": MODEL
        }

        if contact_name not in st.session_state.contacts:
            st.session_state.contacts[contact_name] = {
                "context": "family",
                "history": [],
                "created_at": datetime.datetime.now().isoformat(),
                "id": None
            }

        st.session_state.contacts[contact_name]["history"].append(new_message)
        save_message(contact_name, mode, message, response, "calm", healing_score, MODEL)
        st.session_state[f"last_response_{contact_name}"] = {
            "response": response,
            "healing_score": healing_score,
            "timestamp": datetime.datetime.now().timestamp(),
            "model": MODEL
        }
        # Do NOT clear conversation_input_text here. It will be cleared in render_conversation() after rerun.

    except requests.exceptions.Timeout:
        st.session_state.last_error_message = "API request timed out. Please try again. The AI might be busy."
    except requests.exceptions.ConnectionError:
        st.session_state.last_error_message = "Connection error. Please check your internet connection."
    except requests.exceptions.RequestException as e:
        st.session_state.last_error_message = f"Network or API error: {e}. Please check your API key or connection."
    except (KeyError, IndexError) as e:
        st.session_state.last_error_message = f"Received an unexpected response from the AI API. Error: {e}"
    except Exception as e:
        st.session_state.last_error_message = f"An unexpected error occurred: {e}"

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

                # Check if contact already exists before saving to avoid duplicates in this flow
                if contact_name not in st.session_state.contacts:
                    if save_contact(contact_name, context_key):
                        # Reload contacts to get the ID from Supabase for the newly added contact
                        st.session_state.contacts = load_contacts_and_history()
                        st.session_state.active_contact = contact_name
                        st.session_state.page = "conversation"
                        st.rerun()
                else:
                    st.session_state.active_contact = contact_name
                    st.session_state.page = "conversation"
                    st.rerun()


    st.markdown("---")

    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name_input")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="first_time_new_contact_context_select")

        if st.form_submit_button("Add Custom Contact"):
            name_to_add = st.session_state.first_time_new_contact_name_input
            context_to_add = st.session_state.first_time_new_contact_context_select
            if name_to_add.strip():
                if name_to_add not in st.session_state.contacts: # Prevent adding duplicate names
                    if save_contact(name_to_add, context_to_add):
                        st.session_state.contacts = load_contacts_and_history() # Reload to get ID
                        st.session_state.active_contact = name_to_add
                        st.session_state.page = "conversation"
                        st.rerun()
                    else:
                        st.session_state.last_error_message = "Failed to add contact. Please try again."
                else:
                    st.session_state.last_error_message = "Contact with this name already exists."
                    st.rerun() # Rerun to show the error message


# Contact list
def render_contact_list():
    if st.session_state.page != "contacts":
        return

    st.markdown("### 🎙️ The Third Voice")

    # Sort contacts by last message time if available, otherwise by creation time
    sorted_contacts = sorted(
        st.session_state.contacts.items(),
        key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"],
        reverse=True
    )

    for name, data in sorted_contacts:
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start chatting!"
        time_str = last_msg["time"] if last_msg else "New"

        if st.button(
            f"**{name}** | {time_str}\n"
            f"_{preview}_",
            key=f"contact_{name}",
            use_container_width=True
        ):
            st.session_state.active_contact = name
            st.session_state.page = "conversation"
            st.session_state.conversation_input_text = ""
            st.session_state.last_error_message = None
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
        st.session_state.last_error_message = None
        st.rerun()

    # Initialize or reset the input field value when entering edit mode
    # Check if the session state input is empty or doesn't match the current contact's name
    # This prevents the input field from being reset if the user types something and then reruns
    if "edit_contact_name_input" not in st.session_state or st.session_state.edit_contact_name_input == "":
        st.session_state.edit_contact_name_input = contact["name"]
    elif st.session_state.edit_contact_name_input != contact["name"] and st.session_state.edit_contact_name_input == st.session_state.get('initial_edit_contact_name', ''):
        # This handles cases where user navigates back and forth or a rerun occurs
        st.session_state.edit_contact_name_input = contact["name"]

    # Store initial name to detect changes later if needed
    if 'initial_edit_contact_name' not in st.session_state:
        st.session_state.initial_edit_contact_name = contact["name"]
    elif st.session_state.initial_edit_contact_name != contact["name"]:
        # If the active contact changed while on edit page, update initial value
        st.session_state.initial_edit_contact_name = contact["name"]
        st.session_state.edit_contact_name_input = contact["name"] # Also reset the input value


    with st.form("edit_contact_form"):
        name_input = st.text_input("Name",
                                   value=st.session_state.edit_contact_name_input,
                                   key="edit_contact_name_input_widget") # Changed key to avoid conflict

        context_options = list(CONTEXTS.keys())
        initial_context_index = context_options.index(contact["context"]) if contact["context"] in context_options else 0
        context = st.selectbox("Relationship", context_options,
                             index=initial_context_index,
                             format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
                             key="edit_contact_context_select")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                new_name = st.session_state.edit_contact_name_input_widget # Get value from the widget's key
                new_context = st.session_state.edit_contact_context_select

                if not new_name.strip():
                    st.error("Contact name cannot be empty.")
                    st.rerun() # Rerun to display error and keep form state

                # Check for duplicate name if name changed
                if new_name != contact["name"] and new_name in st.session_state.contacts:
                    st.error(f"Contact with name '{new_name}' already exists.")
                    st.rerun()

                if save_contact(new_name, new_context, contact["id"]):
                    st.success(f"Updated {new_name}")
                    # Update active contact if the name changed
                    if st.session_state.active_contact == contact["name"]:
                        st.session_state.active_contact = new_name
                    st.session_state.page = "conversation"
                    st.session_state.edit_contact = None
                    st.session_state.last_error_message = None
                    # Clear edit_contact_name_input_widget for the next edit session
                    st.session_state.edit_contact_name_input = ""
                    st.session_state.initial_edit_contact_name = "" # Reset initial name
                    st.rerun()

        with col2:
            if st.form_submit_button("🗑️ Delete Contact"):
                if delete_contact(contact["id"]):
                    st.success(f"Deleted contact: {contact['name']}")
                    st.session_state.page = "contacts"
                    st.session_state.active_contact = None
                    st.session_state.edit_contact = None
                    st.session_state.last_error_message = None
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
            st.session_state.last_error_message = None
            st.rerun()

    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            # Initialize the input text for the edit screen
            st.session_state.edit_contact_name_input = contact_name
            st.session_state.initial_edit_contact_name = contact_name # Store initial name
            st.session_state.page = "edit_contact"
            st.session_state.last_error_message = None
            st.rerun()

    st.markdown("---")
    st.markdown("#### 💭 Your Input")

    # Use the session_state value directly for the text_area
    user_input_area = st.text_area(
        "What's happening?",
        value=st.session_state.conversation_input_text, # This reads the value for the current render
        key="conversation_input_text",
        placeholder="Share their message or your response...",
        height=120
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", use_container_width=True):
            # Capture the current value from the widget
            input_message = st.session_state.conversation_input_text
            process_message(contact_name, input_message, context)
            # After processing, set the session state variable for the *next* render
            # This will clear the text_area in the subsequent rerun
            st.session_state.conversation_input_text = ""
            st.rerun()
    with col2:
        if st.button("🗑️️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.last_error_message = None
            st.rerun()

    # Display persistent error message here
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)

    st.markdown("---")
    st.markdown("#### 🤖 AI Response")

    last_response_key = f"last_response_{contact_name}"
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        # Display response only if it's recent (e.g., within last 5 minutes)
        # Or if it's the result of the immediate previous action (i.e., not a stale response from a prior session)
        # For simplicity, we'll keep the 5-minute check.
        if datetime.datetime.now().timestamp() - last_resp["timestamp"] < 300: # 5 minutes
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
                    st.caption(f"🤖 Model: {last_resp.get('model', 'Unknown')}")

                if last_resp["healing_score"] >= 8:
                    st.balloons()
        else:
            # If the last response is too old, remove it and prompt for new input
            del st.session_state[last_response_key]
            st.info("💭 Your AI response will appear here after you click Transform")
    else:
        st.info("💭 Your AI response will appear here after you click Transform")

    st.markdown("---")
    st.markdown("#### 📜 Conversation History")

    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total)")

        with st.expander("View Chat History", expanded=False):
            # Displaying last 10 messages for brevity, reversed to show newest at top of history
            for msg in reversed(history):
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
                        disabled=True
                    )
                    st.caption(f"🤖 Model: {msg.get('model', 'Unknown')}")

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
        st.session_state.last_error_message = None
        st.rerun()

    with st.form("add_contact_form"):
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="add_contact_name_input")
        context_options = list(CONTEXTS.keys())
        context_selected_index = context_options.index(st.session_state.add_contact_context_select) if st.session_state.add_contact_context_select in context_options else 0

        context = st.selectbox("Relationship", context_options,
                              index=context_selected_index,
                              format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
                              key="add_contact_context_select")

        if st.form_submit_button("Add Contact"):
            name_to_add = st.session_state.add_contact_name_input
            context_to_add = st.session_state.add_contact_context_select
            if name_to_add.strip():
                if name_to_add not in st.session_state.contacts: # Prevent adding duplicate names
                    if save_contact(name_to_add, context_to_add):
                        st.session_state.contacts = load_contacts_and_history() # Reload to get ID
                        st.success(f"Added {name_to_add}")
                        st.session_state.page = "contacts"
                        st.session_state.add_contact_name_input = ""
                        st.session_state.add_contact_context_select = list(CONTEXTS.keys())[0]
                        st.session_state.last_error_message = None
                        st.rerun()
                    else:
                        st.session_state.last_error_message = "Failed to add contact. Please try again."
                else:
                    st.session_state.last_error_message = "Contact with this name already exists."
                    st.rerun()
            else:
                st.session_state.last_error_message = "Contact name cannot be empty."
                st.rerun()

# Main app
def main():
    st.set_page_config(page_title="The Third Voice", layout="wide")
    initialize_session()

    if not st.session_state.contacts:
        render_first_time_screen()
    else:
        if st.session_state.page == "contacts":
            render_contact_list()
        elif st.session_state.page == "edit_contact":
            render_edit_contact()
        elif st.session_state.page == "add_contact":
            render_add_contact()
        elif st.session_state.page == "conversation":
            render_conversation()

if __name__ == "__main__":
    main()
