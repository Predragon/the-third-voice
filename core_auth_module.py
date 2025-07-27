# --- UI Rendering Functions ---
def render_first_time_screen():
    st.title("👋 Welcome to The Third Voice")
    st.markdown("""
    **Choose a relationship type to begin healing:**
    """)
    
    cols = st.columns(2)
    for i, (context_key, context_info) in enumerate(CONTEXTS.items()):
        with cols[i % 2]:
            if st.button(
                f"{context_info['icon']} {context_key.title()}",
                key=f"ctx_{context_key}",
                help=context_info['description']
            ):
                default_names = {
                    "romantic": "Partner",
                    "coparenting": "Co-parent",
                    "workplace": "Colleague",
                    "family": "Family Member",
                    "friend": "Friend"
                }
                contact_name = default_names.get(context_key, "New Contact")
                if save_contact(contact_name, context_key):
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()

def render_contacts_list_view():
    if not st.session_state.contacts:
        st.info("No contacts yet. Add your first contact to begin healing.")
        if st.button("➕ Add Contact"):
            st.session_state.app_mode = "add_contact_view"
            st.rerun()
        return

    for name, data in st.session_state.contacts.items():
        if st.button(
            f"{CONTEXTS[data['context']]['icon']} {name}",
            key=f"contact_{name}",
            use_container_width=True
        ):
            st.session_state.active_contact = name
            st.session_state.app_mode = "conversation_view"
            st.rerun()

def render_add_contact_view():
    with st.form("add_contact"):
        name = st.text_input("Name")
        context = st.selectbox(
            "Relationship Type",
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}"
        )
        if st.form_submit_button("Save"):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.app_mode = "contacts_list"
                    st.rerun()

def render_edit_contact_view():
    if not st.session_state.get('edit_contact'):
        st.session_state.app_mode = "contacts_list"
        st.rerun()
    
    contact = st.session_state.edit_contact
    with st.form("edit_contact"):
        name = st.text_input("Name", value=contact['name'])
        context = st.selectbox(
            "Relationship",
            list(CONTEXTS.keys()),
            index=list(CONTEXTS.keys()).index(contact['context'])
        )
        if st.form_submit_button("Save"):
            if name.strip():
                if save_contact(name.strip(), context, contact['id']):
                    st.session_state.app_mode = "contacts_list"
                    st.rerun()

# --- Database Operations ---
def save_contact(name, context, contact_id=None):
    user_id = get_current_user_id()
    if not user_id: return False
    
    contact_data = {
        "name": name,
        "context": context,
        "user_id": user_id
    }
    
    try:
        if contact_id:
            supabase.table("contacts").update(contact_data).eq("id", contact_id).execute()
        else:
            supabase.table("contacts").insert(contact_data).execute()
        return True
    except Exception as e:
        st.error(f"Save failed: {str(e)}")
        return False
