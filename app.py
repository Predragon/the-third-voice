import streamlit as st
import json
import datetime
import requests
from supabase import create_client
from uuid import uuid4

# --- Configuration ---
CONTEXTS = ["romantic", "coparenting", "workplace", "family", "friend"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-2-9b-it:free"
MODELS = st.secrets["openrouter"]["models"]
API_KEY = st.secrets["openrouter"]["api_key"]

# --- Supabase ---
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase = create_client(supabase_url, supabase_key)

# --- Initialize Session ---
def initialize_session():
    st.session_state.setdefault("contacts", load_contacts())
    if st.session_state["contacts"]:
        st.session_state.setdefault("active_contact", list(st.session_state["contacts"].keys())[0])
    st.session_state.setdefault("journal_entries", {})
    st.session_state.setdefault("feedback_data", {})
    st.session_state.setdefault("active_mode", "coach")
    st.session_state.setdefault("input_text", "")

def load_contacts():
    try:
        data = supabase.table("contacts").select("*").eq("user_id", get_user_id()).execute().data
        contacts = {}
        for row in data:
            name = row["name"]
            contacts[name] = {"context": row.get("context", "family"), "created_at": row["created_at"], "history": []}
        # Load messages
        messages = supabase.table("messages").select("*").eq("user_id", get_user_id()).execute().data
        for msg in messages:
            contact = msg["contact_name"]
            if contact in contacts:
                contacts[contact]["history"].append(msg)
        return contacts
    except Exception as e:
        st.warning(f"⚠️ Couldn't load contacts: {e}")
        return {}

def get_user_id():
    # Placeholder: Replace with actual auth.uid() from Supabase session if needed
    return st.secrets.get("supabase_user_id", "demo-user-1234")

initialize_session()

# --- Sidebar ---
def contact_sidebar():
    st.sidebar.title("👥 Contacts")
    with st.sidebar.expander("➕ Add Contact"):
        new_name = st.text_input("Name")
        new_context = st.selectbox("Context", CONTEXTS, key="context_select")
        if st.button("Add") and new_name:
            if new_name not in st.session_state.contacts:
                # Save to Supabase
                supabase.table("contacts").insert({
                    "id": str(uuid4()),
                    "name": new_name,
                    "context": new_context,
                    "user_id": get_user_id()
                }).execute()
                st.session_state.contacts[new_name] = {"context": new_context, "history": []}
                st.session_state.active_contact = new_name
                st.success(f"Added {new_name}")
                st.rerun()
            else:
                st.warning("Contact already exists")

    options = list(st.session_state.contacts.keys())
    if options:
        selected = st.sidebar.selectbox("Select", options, index=options.index(st.session_state.active_contact))
        st.session_state.active_contact = selected

contact_sidebar()

# --- AI Request ---
def query_ai(model, contact_name, context, message, mode="coach"):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant aiding with {context} communication."},
            {"role": "user", "content": message}
        ]
    }
    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        result = res.json()["choices"][0]["message"]["content"]
        return result
    except Exception as e:
        return None

def get_cached_response(contact_name, message, context, model):
    try:
        data = supabase.table("ai_response_cache").select("response").match({
            "user_id": get_user_id(),
            "contact_name": contact_name,
            "message": message,
            "model": model
        }).limit(1).execute().data
        return data[0]["response"] if data else None
    except:
        return None

def cache_response(contact_name, message, context, response, model):
    supabase.table("ai_response_cache").insert({
        "id": str(uuid4()),
        "user_id": get_user_id(),
        "contact_name": contact_name,
        "message": message,
        "context": context,
        "response": response,
        "model": model
    }).execute()

# --- Main Logic ---
def render_main():
    contact = st.session_state.active_contact
    context = st.session_state.contacts[contact]["context"]

    st.title(f"🎙️ The Third Voice — {contact}")
    st.caption(f"Relationship Context: *{context}*")

    # Chat History
    st.subheader("📜 Conversation History")
    for msg in reversed(st.session_state.contacts[contact]["history"]):
        with st.expander(f"[{msg['timestamp'][:16]}] {msg['type'].capitalize()}"):
            st.markdown(f"**🧍 You:** {msg['original']}")
            st.markdown(f"**🤖 AI:** {msg['result']}")

    st.subheader("💬 New Message")
    input_text = st.text_area("What do you want help with?", key="input_text")

    if st.button("Send") and input_text.strip():
        model_used = None
        response = None

        # Check cache or try models in order
        for model in MODELS:
            cached = get_cached_response(contact, input_text, context, model)
            if cached:
                response = cached
                model_used = model
                break
            result = query_ai(model, contact, context, input_text)
            if result:
                response = result
                model_used = model
                cache_response(contact, input_text, context, response, model)
                break

        if response:
            msg_id = str(uuid4())
            now = datetime.datetime.now().isoformat()
            supabase.table("messages").insert({
                "id": msg_id,
                "contact_name": contact,
                "user_id": get_user_id(),
                "type": "coach",
                "original": input_text,
                "result": response,
                "timestamp": now,
                "model": model_used
            }).execute()
            st.session_state.contacts[contact]["history"].append({
                "id": msg_id,
                "type": "coach",
                "original": input_text,
                "result": response,
                "timestamp": now,
                "model": model_used
            })
            st.success("✅ Response saved")
            st.session_state.input_text = ""
            st.rerun()
        else:
            st.error("❌ All models failed. Try again later.")

render_main()
