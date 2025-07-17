"""
The Third Voice - Coded with love and hope.
Created by Predrag Mirkovic, for Samantha and every family that deserves a second chance.
"""

import streamlit as st
import streamlit.components.v1 as components
import js_snippets
import json
import datetime

# --- JavaScript/localStorage integration ---
components.html(f"<script>{js_snippets.PERSISTENCE_JS}</script>", height=0)

st.markdown('<input type="hidden" data-token="true" />', unsafe_allow_html=True)
st.markdown('<textarea style="display:none" data-contacts="true"></textarea>', unsafe_allow_html=True)
st.markdown('<textarea style="display:none" data-setup="true"></textarea>', unsafe_allow_html=True)

# -- Default onboarding template: sample contacts/messages --
SAMPLE_CONTACTS = {
    "Family (Demo)": {
        "context": "family",
        "history": [
            {"timestamp": "2025-07-18T10:00:00Z", "message": "Hi, can we talk about our weekend plans?"},
            {"timestamp": "2025-07-18T10:02:00Z", "message": "Of course! I appreciate you reaching out."}
        ]
    },
    "Co-parenting Example": {
        "context": "coparenting",
        "history": [
            {"timestamp": "2025-07-18T09:00:00Z", "message": "Let's coordinate Samantha's school schedule."},
            {"timestamp": "2025-07-18T09:02:00Z", "message": "Yes, can you drop her off Monday?"}
        ]
    }
}

# -- Streamlit state defaults --
if "contacts" not in st.session_state or not st.session_state["contacts"]:
    st.session_state["contacts"] = SAMPLE_CONTACTS.copy()
if "active_contact" not in st.session_state:
    st.session_state["active_contact"] = list(st.session_state["contacts"].keys())[0]
if "setup" not in st.session_state:
    st.session_state["setup"] = {}
if "token_validated" not in st.session_state:
    st.session_state["token_validated"] = False
if "first_visit" not in st.session_state:
    st.session_state["first_visit"] = True

# -- Token gate --
st.title("The Third Voice")
if not st.session_state['token_validated']:
    st.warning("🔐 Enter your token to continue.")
    token = st.text_input("Token:", type="password")
    if st.button("Validate"):
        if token and token.startswith("ttv-"):
            st.session_state['token_validated'] = True
            components.html(f"<script>window.parent.postMessage({{type:'save',token:'{token}'}},'*');</script>", height=0)
            st.rerun()
        else:
            st.error("Invalid token")
    st.stop()

# -- User Onboarding: Show welcome/help screen on first arrival --
if st.session_state["first_visit"]:
    st.markdown("""
    ## 👋 Welcome to The Third Voice!
    Try the demo conversations below, or create your own.
    - Select a contact from the sidebar.
    - Edit or add sample messages to see how the Third Voice works.
    - All your data is private, saved only on this device, and can be cleared at any time.
    """)
    st.session_state["first_visit"] = False

# -- Contacts sidebar --
st.sidebar.title("Contacts")
contacts = st.session_state["contacts"]
active = st.sidebar.radio(
    "Choose a contact:",
    list(contacts.keys()),
    index=list(contacts.keys()).index(st.session_state["active_contact"]),
)
st.session_state["active_contact"] = active

if st.sidebar.button("➕ Add new contact"):
    new_contact = f"Contact {len(contacts)+1}"
    contacts[new_contact] = {"context": "general", "history": []}
    st.session_state["active_contact"] = new_contact

if st.sidebar.button("🗑️ Delete this contact"):
    if len(contacts) > 1:
        contacts.pop(active)
        st.session_state["active_contact"] = list(contacts.keys())[0]

# -- Main: Conversation history for current contact --
st.header(f"Conversation: {st.session_state['active_contact']}")
history = contacts[st.session_state["active_contact"]]["history"]

for entry in history:
    st.markdown(f"• *{entry['timestamp'][:16]}* — {entry['message']}")

new_msg = st.text_input("Type a new message", key="msg")
if st.button("Send message", key="send"):
    if new_msg.strip():
        history.append(
            {"timestamp": datetime.datetime.now().isoformat(), "message": new_msg.strip()}
        )
        st.session_state["contacts"][st.session_state["active_contact"]]["history"] = history
        # Save to localStorage via JS
        components.html(f"<script>window.parent.postMessage({{type:'save',contacts:{json.dumps(st.session_state['contacts'])}}},'*');</script>", height=0)
        st.experimental_rerun()

if st.button("Clear conversation"):
    contacts[st.session_state["active_contact"]]["history"] = []
    components.html(f"<script>window.parent.postMessage({{type:'save',contacts:{json.dumps(st.session_state['contacts'])}}},'*');</script>", height=0)
    st.experimental_rerun()

# -- Data export/import (settings + history) --
st.markdown("### Data Backup / Restore")
uploaded = st.file_uploader("🔼 Upload a backup JSON file:", type="json")
if uploaded:
    try:
        data = json.load(uploaded)
        st.session_state["contacts"] = data.get("contacts", SAMPLE_CONTACTS.copy())
        st.session_state["setup"] = data.get("setup", {})
        components.html(
            f"<script>window.parent.postMessage({{type:'save',contacts:{json.dumps(st.session_state['contacts'])},setup:{json.dumps(st.session_state['setup'])}}},'*');</script>",
            height=0
        )
        st.success("Backup imported!")
        st.experimental_rerun()
    except:
        st.error("Invalid file format.")

if st.button("Download my data (history + setup)"):
    payload = {
        "contacts": st.session_state["contacts"],
        "setup": st.session_state["setup"],
        "saved_at": datetime.datetime.now().isoformat(),
    }
    st.download_button(
        "Click to download your data",
        data=json.dumps(payload, indent=2),
        file_name="third_voice_data.json",
        mime="application/json",
    )

st.caption("Built for resilience and hope. All data stays ONLY on your device unless you export.")
