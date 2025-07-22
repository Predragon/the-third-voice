# Replace the conversation history section with this enhanced version:

def render_conversation():
    if st.session_state.page != "conversation" or not st.session_state.active_contact:
        return
    
    contact_name = st.session_state.active_contact
    context = st.session_state.contacts[contact_name]["context"]
    history = st.session_state.contacts[contact_name]["history"]
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    
    if st.button("← Back", key="back_btn", use_container_width=True):
        st.session_state.page = "contacts"
        st.session_state.active_contact = None
        st.rerun()
    
    # Enhanced History Display
    st.markdown("---")
    st.markdown(f"**Chat History** ({len(history)} messages)")
    
    if history:
        # Show more messages and expand by default
        with st.expander("Recent Messages", expanded=True):  # ← Now expanded by default
            # Show last 10 messages instead of 3
            for msg in reversed(history[-10:]):  # ← Show more messages
                emotion_info = EMOTIONAL_STATES.get(msg['emotional_state'], EMOTIONAL_STATES['calm'])
                
                # Create a more detailed display
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
    
    # Rest of your conversation UI...
    st.write("**How are you feeling?**")
    cols = st.columns(4)
    for i, (state, info) in enumerate(EMOTIONAL_STATES.items()):
        with cols[i % 4]:
            if st.button(f"{info['icon']} {state.title()}", key=f"emotion_{state}", use_container_width=True):
                st.session_state.current_emotional_state = state
                st.rerun()
    
    user_input = st.text_area("What's happening?", key="conversation_input", 
                             placeholder="Share their message or your response...", height=120)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", 
                    disabled=not user_input.strip(), use_container_width=True):
            process_message(contact_name, user_input, context)
    with col2:
        if st.button("🗑️ Clear", key="clear_input", use_container_width=True):
            st.session_state.conversation_input = ""

# Also add a debug function to check if data is loading:
def debug_data():
    """Add this temporarily to debug data loading"""
    st.sidebar.markdown("### Debug Info")
    st.sidebar.write(f"Contacts loaded: {len(st.session_state.contacts)}")
    
    if st.session_state.active_contact:
        contact_name = st.session_state.active_contact
        history_count = len(st.session_state.contacts[contact_name]["history"])
        st.sidebar.write(f"Messages for {contact_name}: {history_count}")
        
        # Show raw data structure
        if st.sidebar.button("Show Raw Data"):
            st.sidebar.json(st.session_state.contacts[contact_name])

# Add this to your main() function temporarily:
def main():
    st.set_page_config(page_title="The Third Voice", layout="wide")
    initialize_session()
    
    # Add debug info temporarily
    debug_data()  # ← Add this line
    
    render_contact_list()
    render_conversation()
    render_add_contact()
