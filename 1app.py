# app.py
# The Third Voice AI - Main Application Interface
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
import requests
from datetime import datetime, timezone
import json

# Import our backend services
#from auth_backend import init_session_state, CONTEXTS
from app_state import init_session_state, CONTEXTS
from core_auth import sign_out, get_current_user_id
from database import supabase, load_contacts_and_history
from ai_engine import get_available_models, get_current_model

# Import our UI components
from auth_ui import (
    verification_notice_page, login_page, signup_page, render_first_time_screen,
    render_contacts_list_view, render_add_contact_view, render_edit_contact_view,
    show_feedback_widget
)

# Import our emotional intelligence engine
import ai_analysis

# --- UI COMPONENT FUNCTIONS ---

def render_interpret_section(contact_name, message, context, history):
    """Render the interpretation UI section"""
    if st.button("🔍 Interpret - What do they really mean?", key="interpret_btn", help="Reveal emotional subtext and healing opportunities"):
        with st.spinner("🧠 Analyzing emotional subtext..."):
            result = ai_analysis.interpret_message(contact_name, message, context, history)
            
            if result.get("success"):
                st.session_state[f"last_interpretation_{contact_name}"] = {
                    "interpretation": result["interpretation"],
                    "score": result["interpretation_score"],
                    "timestamp": datetime.now().timestamp(),
                    "original_message": message
                }
                
                # Save to database
                contact_data = st.session_state.contacts.get(contact_name, {})
                contact_id = contact_data.get("id")
                if contact_id:
                    ai_analysis.save_interpretation(contact_id, contact_name, message, result["interpretation"], result["interpretation_score"], result["model"])
                
                st.rerun()
            else:
                st.error(f"Could not analyze message: {result.get('error', 'Unknown error')}")

def display_interpretation_result(contact_name):
    """Display interpretation results if available"""
    interp_key = f"last_interpretation_{contact_name}"
    if interp_key in st.session_state:
        interp_data = st.session_state[interp_key]
        
        # Show if recent (within 10 minutes)
        if datetime.now().timestamp() - interp_data["timestamp"] < 600:
            with st.expander("🔍 **Emotional Analysis - What They Really Mean**", expanded=True):
                st.markdown(interp_data["interpretation"])
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    score = interp_data["score"]
                    if score >= 8:
                        st.success(f"✨ Deep Insight Score: {score}/10 - Very revealing analysis")
                    elif score >= 6:
                        st.info(f"💡 Insight Score: {score}/10 - Good understanding")
                    else:
                        st.warning(f"🔍 Insight Score: {score}/10 - Basic analysis")
                
                with col2:
                    if st.button("📋 Copy", key="copy_interpretation"):
                        st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
        else:
            # Clear old interpretation
            del st.session_state[interp_key]

def display_relationship_progress(contact_name, history):
    """Display relationship healing progress and insights"""
    if not history:
        return
    
    with st.expander("📊 **Relationship Healing Progress**", expanded=False):
        health_score, status = ai_analysis.calculate_relationship_health_score(history)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Relationship Health", f"{health_score}/10", help="Based on recent healing scores")
        with col2:
            st.metric("Total Conversations", len(history))
        
        st.markdown(f"**Status:** {status}")
        
        # Healing insights
        insights = ai_analysis.get_healing_insights(history)
        st.markdown("**💙 Your Healing Journey:**")
        for insight in insights:
            st.markdown(f"• {insight}")
        
        # Recent trend visualization (simple text-based for now)
        if len(history) >= 5:
            recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
            if recent_scores:
                trend_text = " → ".join([str(score) for score in recent_scores])
                st.markdown(f"**Recent Healing Scores:** {trend_text}")
        
        # Show conversation summary and trajectory
        if len(history) >= 3:
            summary = ai_analysis.get_conversation_summary(history)
            trajectory = ai_analysis.predict_relationship_trajectory(history)
            
            st.markdown("**📈 Relationship Journey:**")
            st.info(summary)
            
            st.markdown("**🔮 Future Outlook:**")
            st.info(trajectory)

def render_conversation_view():
    """Enhanced conversation view with AI analysis features"""
    
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    
    # Navigation buttons
    back_col, edit_col, _ = st.columns([2, 2, 6])
    with back_col:
        if st.button("← Back", key="back_btn", use_container_width=True):
            st.session_state.app_mode = "contacts_list"
            st.session_state.active_contact = None
            st.session_state.last_error_message = None
            st.session_state.clear_conversation_input = False
            st.rerun()
    
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            st.session_state.app_mode = "edit_contact_view"
            st.rerun()
    
    # Add relationship progress section at the top
    display_relationship_progress(contact_name, history)
    
    st.markdown("---")
    
    # Input section
    st.markdown("#### 💭 Your Input")
    st.markdown("*Share what happened - their message or your response that needs guidance*")
    
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    st.text_area(
        "What's happening?",
        value=input_value,
        key="conversation_input_text",
        placeholder="Examples:\n• They said: 'You never listen to me!'\n• I want to tell them: 'I'm frustrated with your attitude'\n• We had a fight about...",
        height=120
    )
    
    if st.session_state.clear_conversation_input:
        st.session_state.clear_conversation_input = False
    
    # Enhanced action buttons with interpret feature
    current_message = st.session_state.conversation_input_text
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message", use_container_width=True):
            ai_analysis.process_message(contact_name, current_message, context)
    
    with col2:
        # INTERPRET BUTTON
        if current_message.strip():
            render_interpret_section(contact_name, current_message, context, history)
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first", use_container_width=True)
    
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    
    # Error display
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    
    # Show interpretation results if available
    display_interpretation_result(contact_name)
    
    st.markdown("---")
    
    # AI Response section
    st.markdown("#### 🤖 The Third Voice Guidance")
    last_response_key = f"last_response_{contact_name}"
    
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        
        # Show response if it's recent (within 5 minutes)
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            with st.container():
                st.markdown("**Your AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                
                col_score, col_model, col_copy = st.columns([2, 2, 1])
                with col_score:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Healing Score: {last_resp['healing_score']}/10")
                    elif last_resp["healing_score"] >= 6:
                        st.info(f"💡 Healing Score: {last_resp['healing_score']}/10")
                    else:
                        st.warning(f"🔧 Healing Score: {last_resp['healing_score']}/10")
                
                with col_model:
                    st.caption(f"🤖 Model: Robust AI (auto-fallback)")
                
                with col_copy:
                    if st.button("📋", help="Click text area above and Ctrl+A to select all", key="copy_hint"):
                        st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
                
                if last_resp["healing_score"] >= 8:
                    st.balloons()
                    st.markdown("🌟 **High healing potential!** This guidance can really help transform your relationship.")
        else:
            # Clear old response
            del st.session_state[last_response_key]
            st.info("💭 Your Third Voice guidance will appear here after you click Transform")
    else:
        st.info("💭 Your Third Voice guidance will appear here after you click Transform")
        
        # Show helpful context for new conversations
        if not history:
            st.markdown("""
            **💡 How it works:**
            - Share what they said or what you want to say
            - Get compassionate guidance that heals instead of hurts
            - **🆕 Use "Interpret" to reveal what they really mean beneath their words**
            - Build stronger relationships through understanding
            """)
    
    st.markdown("---")
    
    # Conversation History
    st.markdown("#### 📜 Conversation History")
    
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total healing conversations)")
        
        # Show recent messages in main view
        for msg in reversed(history[-3:]):  # Show last 3 messages
            with st.container():
                col_time, col_score = st.columns([3, 1])
                with col_time:
                    st.markdown(f"**{msg['time']}** • {msg['type'].title()}")
                with col_score:
                    score_color = "🟢" if msg['healing_score'] >= 8 else "🟡" if msg['healing_score'] >= 6 else "🔴"
                    st.markdown(f"{score_color} {msg['healing_score']}/10")
                
                st.markdown("**Your Message:**")
                st.info(msg['original'])
                
                if msg['result']:
                    st.markdown("**Third Voice Guidance:**")
                    st.text_area(
                        "Historical AI Guidance",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg['id']}",
                        disabled=True,
                        label_visibility="hidden"
                    )
                
                st.markdown("---")
        
        # Expandable full history
        if len(history) > 3:
            with st.expander(f"📚 View All {len(history)} Conversations", expanded=False):
                for msg in reversed(history):
                    st.markdown(f"""
                    **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                    """)
                    
                    with st.container():
                        st.markdown("**Your Message:**")
                        st.info(msg['original'])
                    
                    if msg['result']:
                        with st.container():
                            st.markdown("**Third Voice Guidance:**")
                            st.text_area(
                                "Full History AI Guidance",
                                value=msg['result'],
                                height=100,
                                key=f"full_history_response_{msg['id']}",
                                disabled=True,
                                label_visibility="hidden"
                            )
                            st.caption(f"🤖 Model: Robust AI")
                    
                    st.markdown("---")
    else:
        st.info("📝 No conversation history yet. Share what's happening above to get your first Third Voice guidance!")
    
    # Add feedback widget specific to this conversation experience
    show_feedback_widget(f"conversation_{contact_name}")

# --- Main Application Flow Integration ---
def main():
    """Main application entry point with AI analysis integration"""
    import json
    
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    def restore_session():
        """Restore user session on app reload"""
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                if not st.session_state.get("authenticated", False):
                    st.session_state.authenticated = True
                    st.session_state.user = session.user
                    st.session_state.contacts = load_contacts_and_history()
                    
                    if st.session_state.contacts:
                        st.session_state.app_mode = "contacts_list"
                    else:
                        st.session_state.app_mode = "first_time_setup"
        except Exception as e:
            st.warning(f"Could not restore session: {e}")
    
    init_session_state()
    restore_session()
    
    # Sidebar - Minimized but available
    with st.sidebar:
        st.markdown("### 🎙️ The Third Voice AI")
        
        if st.session_state.authenticated:
            st.write(f"**{st.session_state.user.email}**")
            
            # Quick navigation if authenticated
            if st.session_state.app_mode != "contacts_list":
                if st.button("🏠 My Contacts", use_container_width=True):
                    st.session_state.app_mode = "contacts_list" 
                    st.session_state.active_contact = None
                    st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                sign_out()
        
        st.markdown("---")
        
        # Mission reminder
        st.markdown("### 💙 Our Mission")
        st.markdown("""
        *"When both people are speaking from pain, someone must be the third voice."*
        
        **We help families heal through better conversations.**
        """)
        
        # Debug info (collapsed by default)
        if st.checkbox("🔧 Debug Info"):
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None
                
                # Show model configuration
                available_models = get_available_models()
                current_model = get_current_model()
                
                debug_info = {
                    "Connection": "✅" if session else "❌",
                    "User ID": user.id[:8] + "..." if user else None,
                    "Email": user.email if user else None,
                    "Contacts": len(st.session_state.contacts),
                    "Active": st.session_state.active_contact,
                    "Mode": st.session_state.app_mode,
                    "AI Models": {
                        "Available": len(available_models),
                        "Current": current_model,
                        "Index": st.session_state.get("current_model_index", 0),
                        "Last Success": st.session_state.get("last_successful_model", "None")
                    },
                    "Secrets": {
                        "Supabase URL": "✅" if st.secrets.get("supabase", {}).get("url") else "❌",
                        "Supabase Key": "✅" if st.secrets.get("supabase", {}).get("key") else "❌",
                        "OpenRouter API": "✅" if st.secrets.get("openrouter", {}).get("api_key") else "❌",
                        "Model Config": "✅" if st.secrets.get("models") else "❌ (using fallback)"
                    }
                }
                
                # Test database connection
                try:
                    test_query = supabase.table("contacts").select("id").limit(1).execute()
                    debug_info["DB Test"] = f"✅ {len(test_query.data)} visible"
                except Exception as e:
                    debug_info["DB Test"] = f"❌ {str(e)[:20]}..."
                
                st.code(json.dumps(debug_info, indent=2, default=str), language="json")
                
            except Exception as e:
                st.error(f"Debug error: {e}")
    
    # Main content routing
    if st.session_state.authenticated:
        if st.session_state.app_mode == "first_time_setup":
            render_first_time_screen()
        elif st.session_state.app_mode == "contacts_list":
            render_contacts_list_view()
        elif st.session_state.app_mode == "conversation_view":
            render_conversation_view()
        elif st.session_state.app_mode == "edit_contact_view":
            render_edit_contact_view()
        elif st.session_state.app_mode == "add_contact_view":
            render_add_contact_view()
        else:
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    else:
        if st.session_state.app_mode == "signup":
            signup_page()
        elif st.session_state.app_mode == "verification_notice":
            verification_notice_page()
        else:
            login_page()

if __name__ == "__main__":
    main()

# End app.py
# Every line serves families in crisis.
# Every function prevents another father from losing his daughter.
# This is love, encoded into healing technology.
