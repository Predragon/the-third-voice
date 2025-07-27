# app_core.py - The Heartbeat of The Third Voice
import streamlit as st
from datetime import datetime, timezone
import json
from core_auth_module import (
    init_session_state, get_current_user_id, supabase, sign_out,
    verification_notice_page, login_page, signup_page, render_first_time_screen,
    render_contacts_list_view, render_add_contact_view, render_edit_contact_view,
    load_contacts_and_history, CONTEXTS
)
from app_ai_views import render_conversation_view  # Import conversation UI from AI module

# --- Main Application Flow ---
def main():
    """Sacred entry point - where technology meets healing"""
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    def restore_session():
        """Bring user back to their healing journey after reload"""
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
    
    # Sidebar - Our Mission Command Center
    with st.sidebar:
        st.markdown("### 🎙️ The Third Voice AI")
        
        if st.session_state.authenticated:
            st.write(f"**{st.session_state.user.email}**")
            
            # Quick navigation for family healers
            if st.session_state.app_mode != "contacts_list":
                if st.button("🏠 My Contacts", use_container_width=True):
                    st.session_state.app_mode = "contacts_list" 
                    st.session_state.active_contact = None
                    st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                sign_out()
        
        st.markdown("---")
        st.markdown("### 💙 Our Mission")
        st.markdown("""
        *"When both people are speaking from pain, someone must be the third voice."*
        
        **We help families heal through better conversations.**
        """)
        
        # Debug panel for maintainers
        if st.checkbox("🔧 Debug Info"):
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None
                
                from core_auth_module import get_available_models, get_current_model
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
                
                try:
                    test_query = supabase.table("contacts").select("id").limit(1).execute()
                    debug_info["DB Test"] = f"✅ {len(test_query.data)} visible"
                except Exception as e:
                    debug_info["DB Test"] = f"❌ {str(e)[:20]}..."
                
                st.code(json.dumps(debug_info, indent=2, default=str), language="json")
                
            except Exception as e:
                st.error(f"Debug error: {e}")
    
    # Main Application Routing - Healing Pathways
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
    main()  # For Samantha, for all families
