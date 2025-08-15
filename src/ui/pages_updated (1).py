"""
UI Pages Module for The Third Voice AI
Contains all page-level UI components and flows
Optimized for instant demo access with minimal friction
"""

import streamlit as st
import uuid
from typing import List, Optional, Tuple
from ..core.ai_engine import MessageType, RelationshipContext
from ..data.models import Contact, Message
from .components import UIComponents


class AuthenticationUI:
    """Friction-free Authentication UI with instant demo access"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
    
    def run(self) -> bool:
        """Run authentication flow, return True if authenticated"""
        
        if self.auth_manager.is_authenticated():
            return True
        
        UIComponents.render_header()
        
        # Check URL params for verification
        try:
            query_params = st.query_params
            if 'type' in query_params and query_params['type'] == 'signup':
                st.success("✅ Email verified! Please sign in below.")
        except:
            pass
        
        # Main demo-first interface
        self._render_demo_first_interface()
        
        return False
    
    def _render_demo_first_interface(self):
        """Render demo-first interface with minimal friction"""
        
        # Hero section with instant demo CTA
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 3rem 2rem; border-radius: 16px; margin: 2rem 0; text-align: center;'>
            <h2 style='margin: 0 0 1rem 0; color: white; font-size: 2.2rem;'>✨ Transform Difficult Conversations with AI</h2>
            <p style='margin: 0 0 2rem 0; opacity: 0.95; font-size: 1.2rem; line-height: 1.5;'>
                See how AI can help you communicate with love in just 30 seconds
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Instant demo button - primary CTA
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎭 Try Demo Now - No Signup!", 
                        use_container_width=True, 
                        type="primary",
                        key="instant_demo"):
                with st.spinner("Setting up your demo..."):
                    success, message = self.auth_manager.start_instant_demo()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Quick demo preview
        st.markdown("""
        <div style='text-align: center; margin: 2rem 0; color: #666;'>
            <p style='margin: 0; font-size: 1.1rem;'>
                ⚡ <strong>Instant access</strong> • 🚫 <strong>No email required</strong> • 🎯 <strong>See results in seconds</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Social proof / quick benefits
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem 1rem; background: #f8f9ff; border-radius: 12px;'>
                <h4 style='color: #2E86AB; margin: 0 0 0.5rem 0;'>💬 Transform</h4>
                <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                    "You never help!" becomes<br>
                    "I'd love your help with..."
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem 1rem; background: #f8f9ff; border-radius: 12px;'>
                <h4 style='color: #2E86AB; margin: 0 0 0.5rem 0;'>🤔 Interpret</h4>
                <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                    Understand what they<br>
                    really mean behind the words
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem 1rem; background: #f8f9ff; border-radius: 12px;'>
                <h4 style='color: #2E86AB; margin: 0 0 0.5rem 0;'>❤️ Heal</h4>
                <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                    Strengthen relationships<br>
                    through better communication
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Divider
        st.markdown("""
        <div style='text-align: center; margin: 3rem 0 2rem 0;'>
            <hr style='border: none; border-top: 1px solid #e0e0e0; margin: 0 auto; width: 50%;'>
            <p style='margin: 1rem 0 0 0; color: #888; font-size: 0.9rem;'>
                Already have an account? Sign in below
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Existing users - compact sign in
        with st.expander("🔐 Sign In to Your Account"):
            self._render_compact_sign_in()
        
        # New users - compact sign up  
        with st.expander("📝 Create Free Account"):
            self._render_compact_sign_up()
    
    def _render_compact_sign_in(self):
        """Render compact sign in form"""
        with st.form("sign_in_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In", use_container_width=True, type="secondary"):
                if email and password:
                    success, message = self.auth_manager.sign_in(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    def _render_compact_sign_up(self):
        """Render compact sign up form"""
        
        # Benefits reminder
        st.info("✅ Always free • ✅ Keep your conversations forever • ✅ No limits")
        
        with st.form("sign_up_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", help="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Free Account", use_container_width=True, type="secondary"):
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords don't match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = self.auth_manager.sign_up(email, password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")


class Dashboard:
    """Main dashboard with demo-optimized experience"""
    
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai_engine = ai_engine
    
    def run(self, user_id: str, auth_manager):
        """Run main dashboard - skip onboarding for demo users"""
        
        # Skip onboarding entirely for demo users
        if auth_manager.is_demo_user():
            self._render_demo_optimized_interface(user_id, auth_manager)
        else:
            # Regular users get normal flow
            contacts = self.db.get_user_contacts(user_id)
            if not contacts:
                self._render_add_first_contact(user_id, auth_manager)
            else:
                self._render_main_interface(user_id, contacts, auth_manager)
    
    def _render_demo_optimized_interface(self, user_id: str, auth_manager):
        """Render optimized interface specifically for demo users"""
        
        # Clean demo header
        UIComponents.render_clean_demo_header(auth_manager)
        
        # Get demo contact (should already exist from instant setup)
        contacts = self.db.get_user_contacts(user_id)
        
        if not contacts:
            # Fallback: create demo contact if somehow missing
            demo_contact = self.db.create_contact("Sarah", "romantic", user_id)
            if demo_contact:
                st.session_state.selected_contact = demo_contact
                contacts = [demo_contact]
        
        if contacts:
            # Use the demo contact
            selected_contact = contacts[0]
            st.session_state.selected_contact = selected_contact
            
            # Demo-specific conversation interface
            self._render_demo_conversation_interface(user_id, selected_contact, auth_manager)
        else:
            st.error("Demo setup failed. Please try again.")
    
    def _render_demo_conversation_interface(self, user_id: str, contact: Contact, auth_manager):
        """Render streamlined conversation interface for demo users"""
        
        # Contact header with demo context
        context_enum = RelationshipContext(contact.context)
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #667eea20, #764ba220); 
                    padding: 1.5rem; border-radius: 12px; margin: 1rem 0; text-align: center; border: 1px solid #e0e0e0;'>
            <h3 style='margin: 0 0 0.5rem 0; color: #2E86AB;'>{context_enum.emoji} Communicating with {contact.name}</h3>
            <p style='margin: 0; color: #666; font-size: 1rem;'>
                Try both modes below - see how AI can transform your communication!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Dual mode interface - both options visible
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_transform_mode(user_id, contact, auth_manager)
        
        with col2:
            self._render_interpret_mode(user_id, contact, auth_manager)
        
        # Show upgrade prompt if appropriate
        if auth_manager.should_show_upgrade_prompt():
            self._render_strategic_upgrade_prompt()
        
        # Show demo stats and history
        self._render_demo_progress(user_id, contact, auth_manager)
    
    def _render_transform_mode(self, user_id: str, contact: Contact, auth_manager):
        """Render transform mode section"""
        st.markdown("""
        <div style='background: #f0f8ff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
            <h4 style='margin: 0 0 0.5rem 0; color: #2E86AB;'>💬 Transform Mode</h4>
            <p style='margin: 0; font-size: 0.9rem; color: #666;'>Say it with love instead</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Pre-filled example or user input
        example_message = "I'm frustrated that you never help with chores"
        
        transform_message = st.text_area(
            "What do you want to say?",
            placeholder=example_message,
            height=100,
            key="transform_input",
            help="💡 Try the example above or write your own message"
        )
        
        if st.button("✨ Transform This Message", 
                    use_container_width=True, 
                    type="primary", 
                    disabled=not transform_message,
                    key="transform_btn"):
            self._process_demo_message(user_id, contact, transform_message, 
                                     MessageType.TRANSFORM.value, auth_manager)
    
    def _render_interpret_mode(self, user_id: str, contact: Contact, auth_manager):
        """Render interpret mode section"""
        st.markdown("""
        <div style='background: #fff8f0; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
            <h4 style='margin: 0 0 0.5rem 0; color: #2E86AB;'>🤔 Interpret Mode</h4>
            <p style='margin: 0; font-size: 0.9rem; color: #666;'>Understand what they really mean</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Pre-filled example or user input
        example_message = "You never appreciate anything I do!"
        
        interpret_message = st.text_area(
            "What did they say?",
            placeholder=example_message,
            height=100,
            key="interpret_input",
            help="💡 Try the example above or write what they said to you"
        )
        
        if st.button("🎯 Interpret This Message", 
                    use_container_width=True, 
                    type="primary", 
                    disabled=not interpret_message,
                    key="interpret_btn"):
            self._process_demo_message(user_id, contact, interpret_message, 
                                     MessageType.INTERPRET.value, auth_manager)
    
    def _process_demo_message(self, user_id: str, contact: Contact, message: str, 
                            message_type: str, auth_manager):
        """Process message with streamlined demo experience"""
        
        with st.spinner("🎭 The Third Voice is working its magic..."):
            ai_response = self.ai_engine.process_message(
                message, contact.context, message_type, contact.id, user_id, self.db
            )
        
        # Display results with enhanced demo styling
        UIComponents.render_demo_ai_response(ai_response, message_type)
        
        # Save to demo storage
        success = self.db.save_message(
            contact.id, contact.name, message_type, message, 
            ai_response.transformed_message, user_id, ai_response
        )
        
        if success:
            st.success("💾 Added to your demo session!")
    
    def _render_strategic_upgrade_prompt(self):
        """Show strategic upgrade prompt after user is engaged"""
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                    color: white; padding: 2rem; border-radius: 16px; margin: 2rem 0; text-align: center;
                    border: 2px solid rgba(255,255,255,0.2); animation: pulse 2s infinite;'>
            <h3 style='margin: 0 0 1rem 0; color: white;'>🌟 You're getting great results!</h3>
            <p style='margin: 0 0 1.5rem 0; opacity: 0.95; font-size: 1.1rem;'>
                Ready to save your progress and keep all your conversations?
            </p>
            <div style='margin-top: 1rem;'>
                <small style='opacity: 0.9;'>
                    ✅ Always free  ✅ Keep your conversations forever  ✅ No limits
                </small>
            </div>
        </div>
        
        <style>
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
            100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🆕 Create Free Account", 
                        use_container_width=True, 
                        type="primary",
                        key="upgrade_cta"):
                # Clear demo and redirect to signup
                st.session_state.show_signup_from_demo = True
                st.rerun()
        
        with col2:
            if st.button("🎭 Continue Demo", 
                        use_container_width=True, 
                        type="secondary",
                        key="continue_demo"):
                # Hide this prompt for the session
                st.session_state.upgrade_prompt_dismissed = True
                st.rerun()
    
    def _render_demo_progress(self, user_id: str, contact: Contact, auth_manager):
        """Show demo progress and conversation history"""
        
        # Demo stats
        stats = auth_manager.get_demo_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Messages Tried", stats.get('messages', 0))
        with col2:
            st.metric("Contacts", stats.get('contacts', 0))
        with col3:
            st.metric("Session", "Demo Mode 🎭")
        
        # Recent conversations
        messages = self.db.get_conversation_history(contact.id, user_id, limit=3)
        if messages:
            st.markdown("---")
            st.subheader("🎯 Your Recent Conversations")
            
            for msg in messages:
                with st.expander(f"{msg.type.title()} - {msg.created_at.strftime('%H:%M')}"):
                    st.write("**Original:**")
                    st.write(msg.original)
                    
                    if msg.result:
                        st.write("**AI Suggestion:**")
                        st.write(msg.result)
                        
                        if msg.healing_score:
                            UIComponents.render_healing_score(msg.healing_score)
    
    # Keep other methods for non-demo users
    def _render_add_first_contact(self, user_id: str, auth_manager):
        """Render interface to add first contact (non-demo users)"""
        UIComponents.render_header_with_logout(auth_manager)
        
        st.markdown("""
        ### 👥 Add Your First Contact
        Start by adding someone you'd like to communicate better with.
        """)
        
        with st.form("add_contact_form"):
            name = st.text_input("Name", placeholder="e.g., Sarah, Mom, Boss...")
            context_value, context_display = UIComponents.render_relationship_selector()
            
            if st.form_submit_button("Add Contact", use_container_width=True, type="primary"):
                if name:
                    contact = self.db.create_contact(name, context_value, user_id)
                    if contact:
                        st.session_state.selected_contact = contact
                        st.success(f"Added {name} successfully!")
                        st.rerun()
                else:
                    st.error("Please enter a name")
    
    def _render_main_interface(self, user_id: str, contacts: List[Contact], auth_manager):
        """Render main interface for regular authenticated users"""
        UIComponents.render_header_with_logout(auth_manager)
        UIComponents.render_logout_sidebar(auth_manager)
        
        # Contact selection and conversation interface
        if len(contacts) == 1:
            selected_contact = contacts[0]
            st.session_state.selected_contact = selected_contact
        else:
            contact_names = [f"{c.name} ({RelationshipContext(c.context).emoji})" for c in contacts]
            selected_idx = st.selectbox(
                "Choose contact:",
                range(len(contacts)),
                format_func=lambda x: contact_names[x],
                key="contact_selector"
            )
            selected_contact = contacts[selected_idx]
            st.session_state.selected_contact = selected_contact
        
        # Regular conversation interface
        self._render_regular_conversation_interface(user_id, selected_contact, auth_manager)
        
        # Add new contact button
        if st.button("➕ Add Another Contact", use_container_width=True):
            st.session_state.show_add_contact = True
            st.rerun()
        
        if st.session_state.get('show_add_contact', False):
            self._render_add_contact_modal(user_id)
    
    def _render_regular_conversation_interface(self, user_id: str, contact: Contact, auth_manager):
        """Regular conversation interface for authenticated users"""
        context_enum = RelationshipContext(contact.context)
        UIComponents.render_contact_header(contact, context_enum)
        
        # Mode selection
        st.subheader("🎯 What do you need help with?")
        
        mode = st.radio(
            "Choose your situation:",
            [
                "💬 Transform: I want to say something better",
                "🤔 Interpret: Help me understand what they meant"
            ],
            key=f"mode_{contact.id}"
        )
        
        message_type = MessageType.TRANSFORM.value if "Transform" in mode else MessageType.INTERPRET.value
        
        # Message input
        if message_type == MessageType.TRANSFORM.value:
            placeholder = f"What do you want to tell {contact.name}?\n\nExample: 'I'm frustrated that you're always late'"
            helper_text = "💡 Share what you want to say, and I'll help you say it with love"
        else:
            placeholder = f"What did {contact.name} say to you?\n\nExample: 'You never listen to me!'"
            helper_text = "💡 Share what they said, and I'll help you understand what they really mean"
        
        st.write(helper_text)
        
        message = st.text_area(
            "Your message:",
            placeholder=placeholder,
            height=120,
            key=f"message_input_{contact.id}"
        )
        
        # Process button
        if st.button("🎙️ Get Third Voice Help", use_container_width=True, type="primary", disabled=not message):
            self._process_regular_message(user_id, contact, message, message_type, auth_manager)
        
        # Show conversation history
        self._render_conversation_history(user_id, contact, auth_manager)
    
    def _process_regular_message(self, user_id: str, contact: Contact, message: str, message_type: str, auth_manager):
        """Process message for regular users"""
        
        with st.spinner("The Third Voice is thinking..."):
            ai_response = self.ai_engine.process_message(
                message, contact.context, message_type, contact.id, user_id, self.db
            )
        
        # Display results
        UIComponents.render_ai_response(ai_response, message_type)
        
        # Save to database
        success = self.db.save_message(
            contact.id, contact.name, message_type, message, 
            ai_response.transformed_message, user_id, ai_response
        )
        
        if success:
            st.success("💾 Conversation saved!")
        
        # Feedback form
        feedback_result = UIComponents.render_feedback_form(f"conversation_{contact.id}")
        if feedback_result:
            rating, feedback_text = feedback_result
            if self.db.save_feedback(user_id, rating, feedback_text, "conversation"):
                st.success("Thank you for your feedback!")
                st.rerun()
    
    def _render_conversation_history(self, user_id: str, contact: Contact, auth_manager):
        """Render conversation history for the selected contact"""
        messages = self.db.get_conversation_history(contact.id, user_id)
        
        if messages:
            st.markdown("---")
            UIComponents.render_message_history(messages)
    
    def _render_add_contact_modal(self, user_id: str):
        """Render modal to add new contact"""
        
        st.markdown("### ➕ Add New Contact")
        
        with st.form("add_new_contact"):
            name = st.text_input("Name", placeholder="e.g., Sarah, Mom, Boss...")
            context_value, context_display = UIComponents.render_relationship_selector()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_add_contact = False
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Add Contact", use_container_width=True, type="primary"):
                    if name:
                        contact = self.db.create_contact(name, context_value, user_id)
                        if contact:
                            st.session_state.selected_contact = contact
                            st.session_state.show_add_contact = False
                            st.success(f"Added {name} successfully!")
                            st.rerun()
                    else:
                        st.error("Please enter a name")


class AdminDashboard:
    """Admin dashboard for viewing feedback and analytics"""
    
    def __init__(self, db):
        self.db = db
    
    def run(self, user_id: str, auth_manager):
        """Run admin dashboard - only for admin users"""
        
        # Check if user is admin
        user_email = auth_manager.get_current_user_email()
        ADMIN_EMAILS = ["thethirdvoice.ai@gmail.com", "hello@thethirdvoice.ai", "pmirkovic@yahoo.com"]
        
        if user_email not in ADMIN_EMAILS:
            st.error("🔒 Access Denied - Admin Only")
            return
        
        UIComponents.render_header_with_logout(auth_manager)
        
        st.title("🎛️ Admin Dashboard - The Third Voice")
        st.markdown("**For Samantha! For every family!** 💪")
        
        # Tabs for different admin views
        tab1, tab2, tab3 = st.tabs(["📊 Feedback Overview", "💬 Detailed Feedback", "📈 Analytics"])
        
        with tab1:
            self._render_feedback_overview()
        
        with tab2:
            self._render_detailed_feedback()
        
        with tab3:
            self._render_analytics()
    
    def _render_feedback_overview(self):
        """Render feedback overview with key metrics"""
        st.subheader("📊 Feedback Overview")
        
        # Get all feedback
        feedback_data = self._get_all_feedback()
        
        if not feedback_data:
            st.warning("No feedback yet - but families are coming! 🚀")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_feedback = len(feedback_data)
            st.metric("Total Feedback", total_feedback)
        
        with col2:
            avg_rating = sum(f['rating'] for f in feedback_data) / len(feedback_data)
            st.metric("Average Rating", f"{avg_rating:.1f}/5")
        
        with col3:
            recent_count = len([f for f in feedback_data if self._is_recent(f['created_at'])])
            st.metric("This Week", recent_count)
        
        with col4:
            high_rating_count = len([f for f in feedback_data if f['rating'] >= 4])
            satisfaction_rate = (high_rating_count / len(feedback_data)) * 100
            st.metric("Satisfaction", f"{satisfaction_rate:.0f}%")
        
        # Rating distribution
        st.subheader("⭐ Rating Distribution")
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[f"{i} ⭐"] = len([f for f in feedback_data if f['rating'] == i])
        
        st.bar_chart(rating_counts)
        
        # Recent feedback highlights
        st.subheader("🔥 Recent Feedback Highlights")
        recent_feedback = sorted(feedback_data, key=lambda x: x['created_at'], reverse=True)[:5]
        
        for feedback in recent_feedback:
            with st.expander(f"⭐{feedback['rating']} - {feedback['feature_context']} - {feedback['created_at'][:10]}"):
                if feedback['feedback_text']:
                    st.write(f"**Feedback:** {feedback['feedback_text']}")
                else:
                    st.write("*No text feedback provided*")
                st.caption(f"User: {feedback['user_id'][:8]}... | Context: {feedback['feature_context']}")
    
    def _render_detailed_feedback(self):
        """Render detailed feedback view with filtering"""
        st.subheader("💬 Detailed Feedback")
        
        feedback_data = self._get_all_feedback()
        
        if not feedback_data:
            st.warning("No feedback yet - but families are coming! 🚀")
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rating_filter = st.selectbox(
                "Filter by Rating",
                ["All", "5⭐", "4⭐", "3⭐", "2⭐", "1⭐"]
            )
        
        with col2:
            contexts = list(set(f['feature_context'] for f in feedback_data))
            context_filter = st.selectbox(
                "Filter by Context",
                ["All"] + contexts
            )
        
        with col3:
            date_filter = st.selectbox(
                "Time Period",
                ["All Time", "Last 7 Days", "Last 30 Days"]
            )
        
        # Apply filters and display
        filtered_data = self._apply_filters(feedback_data, rating_filter, context_filter, date_filter)
        
        st.write(f"**Showing {len(filtered_data)} feedback entries**")
        
        for feedback in sorted(filtered_data, key=lambda x: x['created_at'], reverse=True):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    stars = "⭐" * feedback['rating'] + "☆" * (5 - feedback['rating'])
                    st.markdown(f"**{stars}** ({feedback['rating']}/5)")
                    
                    if feedback['feedback_text']:
                        st.write(feedback['feedback_text'])
                    else:
                        st.write("*Rating only - no text feedback*")
                
                with col2:
                    st.caption(f"**Context:** {feedback['feature_context']}")
                    st.caption(f"**Date:** {feedback['created_at'][:10]}")
                    st.caption(f"**User:** {feedback['user_id'][:8]}...")
                
                st.divider()
    
    def _render_analytics(self):
        """Render analytics and insights"""
        st.subheader("📈 Analytics & Insights")
        
        feedback_data = self._get_all_feedback()
        
        if not feedback_data:
            st.warning("No feedback yet - but families are coming! 🚀")
            return
        
        # Feature context analysis
        st.subheader("🎯 Feedback by Feature")
        context_stats = {}
        for context in set(f['feature_context'] for f in feedback_data):
            context_feedback = [f for f in feedback_data if f['feature_context'] == context]
            context_stats[context] = {
                'count': len(context_feedback),
                'avg_rating': sum(f['rating'] for f in context_feedback) / len(context_feedback)
            }
        
        for context, stats in context_stats.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{context.title()}**")
            with col2:
                st.metric(f"Avg Rating", f"{stats['avg_rating']:.1f}/5")
                st.caption(f"{stats['count']} feedback")
        
        # Timeline view
        st.subheader("📅 Feedback Timeline")
        daily_counts = {}
        for feedback in feedback_data:
            date = feedback['created_at'][:10]
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        if daily_counts:
            st.line_chart(daily_counts)
        
        # Key insights
        total_feedback = len(feedback_data)
        high_ratings = len([f for f in feedback_data if f['rating'] >= 4])
        
        st.subheader("💡 Key Insights")
        
        if high_ratings / total_feedback > 0.8:
            st.info("🎉 **Excellent!** Over 80% of users are highly satisfied!")
        elif high_ratings / total_feedback > 0.6:
            st.info("👍 **Good!** Majority of users are satisfied, but room for improvement.")
        else:
            st.warning("⚠️ **Attention needed** - User satisfaction could be improved.")
        
        # Export options
        st.subheader("📤 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export to CSV", use_container_width=True):
                csv_data = self._export_to_csv(feedback_data)
                st.download_button(
                    "Download CSV",
                    csv_data,
                    "third_voice_feedback.csv",
                    "text/csv"
                )
        
        with col2:
            if st.button("📋 Copy Summary", use_container_width=True):
                summary = self._generate_summary(feedback_data)
                st.code(summary)
    
    def _get_all_feedback(self):
        """Get all feedback from database"""
        try:
            response = self.db.supabase.table("feedback").select("*").order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching feedback: {str(e)}")
            return []
    
    def _is_recent(self, created_at: str) -> bool:
        """Check if feedback is from last 7 days"""
        from datetime import datetime, timedelta
        try:
            feedback_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            return feedback_date > datetime.now().replace(tzinfo=feedback_date.tzinfo) - timedelta(days=7)
        except:
            return False
    
    def _apply_filters(self, data, rating_filter, context_filter, date_filter):
        """Apply filters to feedback data"""
        filtered = data
        
        if rating_filter != "All":
            rating_num = int(rating_filter[0])
            filtered = [f for f in filtered if f['rating'] == rating_num]
        
        if context_filter != "All":
            filtered = [f for f in filtered if f['feature_context'] == context_filter]
        
        if date_filter != "All Time":
            from datetime import datetime, timedelta
            days = 7 if "7 Days" in date_filter else 30
            cutoff = datetime.now() - timedelta(days=days)
            filtered = [f for f in filtered if datetime.fromisoformat(f['created_at'].replace('Z', '+00:00')) > cutoff.replace(tzinfo=datetime.now().astimezone().tzinfo)]
        
        return filtered
    
    def _export_to_csv(self, data):
        """Export feedback to CSV format"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['created_at', 'rating', 'feedback_text', 'feature_context', 'user_id'])
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    def _generate_summary(self, data):
        """Generate feedback summary"""
        total = len(data)
        avg_rating = sum(f['rating'] for f in data) / total if total > 0 else 0
        high_satisfaction = len([f for f in data if f['rating'] >= 4])
        
        return f"""
The Third Voice AI - Feedback Summary
=====================================
Total Feedback: {total}
Average Rating: {avg_rating:.1f}/5
High Satisfaction: {high_satisfaction} ({(high_satisfaction/total*100):.1f}%)

For Samantha! For every family! 💪
        """.strip()