# THE THIRD VOICE - HEALING THROUGH COMMUNICATION
# Fully repaired version with accessible labels and mission-driven UI

import streamlit as st
from modules.session_state import init_session_state
from modules.utils import (
    generate_response,
    get_current_utc_time,
    render_sidebar,
    render_header,
    render_footer,
    render_loading_spinner,
)
from modules.prompts import (
    get_system_prompt,
    get_journal_prompt,
    get_relationship_prompt,
    get_conflict_prompt,
)

def main():
    init_session_state()
    render_sidebar()
    render_header()
    
    # Main tabs - emojis create emotional wayfinding
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Third Voice", 
        "📓 Relationship Journal", 
        "🛠️ Tools", 
        "⚙️ Settings"
    ])

    with tab1:
        render_third_voice_tab()
    
    with tab2:
        render_journal_tab()
    
    with tab3:
        render_tools_tab()
    
    with tab4:
        render_settings_tab()
    
    render_footer()

def render_third_voice_tab():
    st.markdown("""
    <style>
    .stTextArea textarea {
        min-height: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Conflict resolution section
    st.subheader("✌️ Conflict Resolution")
    conflict_context = st.text_area(
        label="Describe the conflict (both perspectives if possible):",
        placeholder="E.g., 'We both feel unheard because...'",
        key="conflict_context"
    )

    if st.button("Find Common Ground", type="primary"):
        with st.spinner("Finding the path forward..."):
            response = generate_response(
                prompt_template=get_conflict_prompt(),
                user_input=conflict_context
            )
            st.markdown(f"**Third Voice:**\n\n{response}")

    # Relationship guidance section
    st.subheader("💞 Relationship Guidance")
    relationship_question = st.text_area(
        label="What relationship challenge are you facing?",
        placeholder="E.g., 'We keep having the same argument about...'",
        key="relationship_question"
    )

    if st.button("Get Guidance", type="secondary"):
        with st.spinner("Seeking wisdom..."):
            response = generate_response(
                prompt_template=get_relationship_prompt(),
                user_input=relationship_question
            )
            st.markdown(f"**Third Voice:**\n\n{response}")

def render_journal_tab():
    journal = st.session_state.get("journal", {})
    
    st.subheader("📝 Daily Reflection")
    journal['date'] = st.date_input(
        label="🗓️ Journal Date",
        value=journal.get('date', None)
    )  # FIXED: Added missing closing parenthesis
    
    st.subheader("✨ What worked well today?")
    journal['what_worked'] = st.text_area(
        label="Positive moments or breakthroughs:",
        value=journal.get('what_worked', ''),
        height=150,
        label_visibility="collapsed"
    )
    
    st.subheader("💔 What didn't work?")
    journal['what_didnt'] = st.text_area(
        label="Challenges or misunderstandings:",
        value=journal.get('what_didnt', ''),
        height=150,
        label_visibility="collapsed"
    )
    
    st.subheader("🔍 New Insights")
    journal['insights'] = st.text_area(
        label="Patterns or realizations:",
        value=journal.get('insights', ''),
        height=150,
        label_visibility="collapsed"
    )
    
    st.subheader("🔄 Behavior Patterns")
    journal['patterns'] = st.text_area(
        label="Recurring themes to address:",
        value=journal.get('patterns', ''),
        height=150,
        label_visibility="collapsed"
    )
    
    if st.button("Save Journal Entry"):
        st.session_state.journal = journal
        st.success("Entry saved at {}".format(get_current_utc_time()))
    
    if st.button("Generate Reflection"):
        with st.spinner("Finding the wisdom in your words..."):
            journal_str = "\n".join(f"{k}: {v}" for k,v in journal.items() if v)
            response = generate_response(
                prompt_template=get_journal_prompt(),
                user_input=journal_str
            )
            st.markdown(f"**Third Voice Reflection:**\n\n{response}")

def render_tools_tab():
    st.subheader("🛠️ Communication Tools")
    # Tools implementation goes here
    st.write("Coming soon: Practical tools for healthier communication")

def render_settings_tab():
    st.subheader("⚙️ Settings")
    # Settings implementation goes here
    st.write("Configuration options will appear here")

if __name__ == "__main__":
    main()
