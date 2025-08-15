"""
App Controller Module for The Third Voice AI
Main application controller that orchestrates all components
Enhanced with demo account support, AI chat, and session persistence
FIXED: Demo users now get AI responses too
"""

import streamlit as st
import traceback
from .components import UIComponents
from .pages import AuthenticationUI, OnboardingFlow, Dashboard, AdminDashboard
from ..auth.demo_manager import DemoManager


class ThirdVoiceApp:
    """Main application controller"""

    def __init__(self, db_manager, ai_engine, auth_manager):
        self.db = db_manager
        self.ai_engine = ai_engine
        self.auth_manager = auth_manager
        self.auth_ui = AuthenticationUI(self.auth_manager)
        self.onboarding = OnboardingFlow(self.db, self.ai_engine)
        self.dashboard = Dashboard(self.db, self.ai_engine)
        self.admin_dashboard = AdminDashboard(self.db)

    def run(self):
        """Main application entry point"""

        # Load custom CSS
        UIComponents.load_custom_css()

        # --- Admin Mode Support ---
        try:
            query_params = st.query_params
            if query_params.get('admin') == ['true']:
                if not self.auth_ui.run():
                    return
                user_id = self.auth_manager.get_current_user_id()
                if user_id:
                    self.admin_dashboard.run(user_id, self.auth_manager)
                return
        except:
            # Fallback for older Streamlit versions
            try:
                query_params = st.experimental_get_query_params()
                if 'admin' in query_params and query_params['admin'][0] == 'true':
                    if not self.auth_ui.run():
                        return
                    user_id = self.auth_manager.get_current_user_id()
                    if user_id:
                        self.admin_dashboard.run(user_id, self.auth_manager)
                    return
            except:
                pass

        # --- Demo Login ---
        if st.button("Use Demo Account"):
            DemoManager.sign_in(self.db)
            st.rerun()

        # Demo warning
        if DemoManager.is_demo():
            st.warning("⚠️ This is a demo account. Messages are not saved, but usage is tracked.")

        # --- Authentication Check ---
        if not DemoManager.is_demo() and not self.auth_ui.run():
            return

        # --- Current User Info ---
        user = getattr(st.session_state, "user", None)
        user_id = user.id if user else self.auth_manager.get_current_user_id()
        user_email = user.email if user else self.auth_manager.get_current_user_email()

        # For demo users, set a demo user_id
        if DemoManager.is_demo():
            user_id = "demo_user"
            user_email = "demo@example.com"

        if not user_id:
            st.error("Authentication error. Please refresh the page.")
            return

        # --- Fetch Contacts ---
        if DemoManager.is_demo():
            # Realistic demo contacts that showcase the app's value
            contacts = [
                {
                    "id": "demo_ex_coparenting", 
                    "name": "💔 Sarah (Ex-Wife)", 
                    "context": "coparenting",
                    "description": "Your ex-wife and co-parent of your 8-year-old daughter. Communication has been tense since the divorce, but you need to coordinate custody and school events."
                },
                {
                    "id": "demo_current_partner", 
                    "name": "💕 Mike (Current Partner)", 
                    "context": "romantic",
                    "description": "Your current boyfriend of 6 months. You're navigating blending families and he sometimes doesn't understand the co-parenting dynamics."
                },
                {
                    "id": "demo_difficult_mother", 
                    "name": "🏠 Mom", 
                    "context": "family",
                    "description": "Your mother who has strong opinions about your divorce and new relationship. She means well but often says hurtful things."
                },
                {
                    "id": "demo_workplace_boss", 
                    "name": "🏢 Jennifer (Boss)", 
                    "context": "workplace",
                    "description": "Your manager who's been unsympathetic about your need for flexible scheduling due to custody arrangements."
                },
                {
                    "id": "demo_supportive_friend", 
                    "name": "🤝 Lisa (Best Friend)", 
                    "context": "friend",
                    "description": "Your best friend since college who's been your rock through the divorce but sometimes gives harsh advice."
                }
            ]
        else:
            try:
                contacts = self.db.get_user_contacts(user_id)
            except Exception as e:
                st.error(f"Error fetching contacts: {e}")
                contacts = []

        # --- Onboarding Check ---
        if not st.session_state.get('onboarding_completed', False):
            if not contacts:
                # Run onboarding for first-time users
                if self.onboarding.run(user_id, self.auth_manager):
                    st.rerun()
                return
            st.session_state.onboarding_completed = True

        # --- Relationship / Contact Selection ---
        st.subheader("Select a Relationship for Context")
        
        # Show contact descriptions for demo
        if DemoManager.is_demo():
            st.info("💡 **Demo Scenario**: You're a single parent navigating complex relationships after divorce. Each contact represents a different communication challenge.")
        
        selected_contact = st.selectbox(
            "Pick a relationship",
            options=contacts,
            format_func=lambda x: x["name"] if isinstance(x, dict) else str(x)
        )

        # Show context description for selected contact
        if DemoManager.is_demo() and isinstance(selected_contact, dict):
            st.markdown(f"**Context**: {selected_contact['description']}")

        # --- Mode Selection ---
        st.subheader("Select Mode")
        mode_choice = st.radio(
            "Choose an action:", 
            ["Transform", "Interpret"],
            help="Transform: Rewrite your message to be more constructive. Interpret: Understand what someone really means and get response suggestions."
        )

        # --- Message Input ---
        st.subheader("Your Message")
        
        # Provide example messages based on selected contact
        if DemoManager.is_demo() and isinstance(selected_contact, dict):
            examples = self._get_example_messages(selected_contact["id"])
            if examples:
                st.markdown("**💡 Try these example messages:**")
                for example in examples:
                    if st.button(f"Use: '{example[:50]}...'", key=f"example_{hash(example)}"):
                        st.session_state.demo_message = example
        
        user_input = st.text_area(
            "Type your message here:", 
            value=st.session_state.get('demo_message', ''),
            key="message_input"
        )
        
        # Clear the demo message after it's been used
        if 'demo_message' in st.session_state:
            del st.session_state.demo_message

        if st.button("Send", type="primary"):
            if user_input.strip():
                try:
                    context = selected_contact["context"] if isinstance(selected_contact, dict) else "friend"
                    contact_id = selected_contact["id"] if isinstance(selected_contact, dict) else "unknown"
                    
                    # FIXED: Process AI for ALL users including demo users
                    with st.spinner("Processing your message..."):
                        ai_response = self.ai_engine.process_message(
                            message=user_input,
                            contact_context=context,
                            message_type=mode_choice.lower(),
                            contact_id=contact_id,
                            user_id=user_id,  # This now works for demo users too
                            db=self.db
                        )

                    # Display AI Response with rich formatting
                    self._display_ai_response(ai_response, mode_choice)

                    # Store messages differently for demo vs regular users
                    if DemoManager.is_demo():
                        # Store in session state for demo
                        DemoManager.add_message(user_input, ai_response.transformed_message, selected_contact, mode_choice)
                    else:
                        # Store in database for regular users
                        try:
                            from ..data.database import save_message
                            save_message(user_email, user_input, ai_response.transformed_message, selected_contact, mode_choice)
                        except Exception as e:
                            st.warning(f"Message processed but not saved to database: {e}")

                except Exception as e:
                    st.error(f"Error processing message: {str(e)}")
                    st.code(traceback.format_exc())

        # --- Display Past Demo Messages ---
        if DemoManager.is_demo() and st.session_state.get('demo_messages', []):
            st.subheader("💬 Demo Chat History (Session Only)")
            for i, msg in enumerate(reversed(st.session_state['demo_messages'])):
                with st.expander(f"{msg['contact']['name']} - {msg['mode']} ({i+1} messages ago)"):
                    st.markdown(f"**Your Original:** {msg['input']}")
                    st.markdown(f"**AI Response:** {msg['response']}")

    def _get_example_messages(self, contact_id):
        """Get example messages for each demo contact"""
        examples = {
            "demo_ex_coparenting": [
                "You're being unreasonable about the school pickup schedule again. This is exactly why our marriage didn't work.",
                "I can't believe you're putting Emma in the middle of this by telling her I'm 'too busy' for her recital.",
                "Your boyfriend doesn't get to make decisions about MY daughter's bedtime routine."
            ],
            "demo_current_partner": [
                "You just don't understand how complicated co-parenting is and you keep making it harder.",
                "I feel like you're jealous of the time I have to spend dealing with Sarah and Emma's needs.",
                "Why can't you just support me instead of always questioning how I handle things with my ex?"
            ],
            "demo_difficult_mother": [
                "I told you that divorce would ruin Emma's life and now look what's happening.",
                "Mike seems nice but you really should focus on fixing your family instead of dating around.",
                "You're being selfish putting your own happiness before your daughter's stability."
            ],
            "demo_workplace_boss": [
                "I can't keep covering for your constant schedule changes because of your personal problems.",
                "Other employees don't get special treatment for their custody arrangements, why should you?",
                "Your productivity has really declined since your divorce and it's affecting the whole team."
            ],
            "demo_supportive_friend": [
                "Honestly, you need to stop letting Sarah walk all over you and stand up for yourself.",
                "Mike is great but maybe you're moving too fast when you should focus on being a single mom.",
                "I'm tired of hearing you complain about the same problems but never taking my advice."
            ]
        }
        return examples.get(contact_id, [])

    def _display_ai_response(self, ai_response, mode_choice):
        """Display AI response with rich formatting"""
        if mode_choice == "Transform":
            st.success("✨ **Transformed Message:**")
            st.write(f"*{ai_response.transformed_message}*")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Healing Score", f"{ai_response.healing_score}/10")
            with col2:
                st.metric("Emotional Tone", ai_response.emotional_state.title())
            
            if ai_response.explanation:
                st.info(f"**Why this helps:** {ai_response.explanation}")
                
        else:  # Interpret
            st.success("🔍 **What they really mean:**")
            if ai_response.subtext:
                st.write(f"**Deeper feelings:** {ai_response.subtext}")
            
            st.success("💬 **Suggested response:**")
            st.write(f"*{ai_response.transformed_message}*")
            
            if ai_response.needs:
                st.write("**Their emotional needs:**")
                for need in ai_response.needs:
                    st.write(f"• {need}")
            
            if ai_response.explanation:
                st.info(f"**Analysis:** {ai_response.explanation}")
        
        # Show model used
        if ai_response.model_used:
            st.caption(f"Response generated by: {ai_response.model_used}")


def run_app():
    """Application entry point function"""
    try:
        from ..data.database import DatabaseManager
        from ..core.ai_engine import AIEngine
        from ..auth.auth_manager import AuthManager

        db = DatabaseManager()
        ai_engine = AIEngine()
        auth_manager = AuthManager(db)

        app = ThirdVoiceApp(db, ai_engine, auth_manager)
        app.run()

    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.code(traceback.format_exc())
