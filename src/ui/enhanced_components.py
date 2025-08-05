"""
Enhanced UI Components Module for The Third Voice AI
Reusable UI components and styling utilities
Enhanced with better sidebar and navigation
"""

import streamlit as st
from typing import List, Optional, Tuple
from ..core.ai_engine import RelationshipContext
from ..data.models import Message, Contact


class UIComponents:
    """Reusable UI components"""
    
    @staticmethod
    def render_header():
        """Render app header"""
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #2E86AB; margin-bottom: 0;'>🎙️ The Third Voice AI</h1>
            <p style='color: #666; font-style: italic; margin-top: 0;'>
                When both people are speaking from pain, someone must be the third voice
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_mobile_header():
        """Render mobile-optimized header"""
        st.markdown("""
        <div style='text-align: center; padding: 0.5rem 0;'>
            <h2 style='color: #2E86AB; margin: 0;'>🎙️ Third Voice</h2>
            <p style='color: #666; font-size: 0.9rem; margin: 0;'>
                Healing conversations with AI
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_header_with_logout(auth_manager):
        """Render header with logout functionality"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("""
            <div style='padding: 0.5rem 0;'>
                <h2 style='color: #2E86AB; margin: 0;'>🎙️ Third Voice</h2>
                <p style='color: #666; font-size: 0.9rem; margin: 0;'>
                    Healing conversations with AI
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # User info and logout
            user_email = auth_manager.get_current_user_email()
            if user_email:
                # Show user email (truncated for mobile)
                display_email = user_email.split('@')[0] if '@' in user_email else user_email
                if len(display_email) > 10:
                    display_email = display_email[:10] + "..."
                
                st.markdown(f"""
                <div style='text-align: right; padding: 0.2rem 0; font-size: 0.8rem; color: #666;'>
                    👤 {display_email}
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚪 Logout", key="logout_header", help="Sign out"):
                auth_manager.sign_out()
                st.rerun()
    
    @staticmethod
    def render_enhanced_sidebar(auth_manager, contacts: List[Contact] = None, current_contact: Contact = None, db=None, user_id: str = None):
        """Render enhanced sidebar with navigation and contact management"""
        
        with st.sidebar:
            # App logo/title
            st.markdown("""
            <div style='text-align: center; padding: 1rem 0; border-bottom: 1px solid #eee; margin-bottom: 1rem;'>
                <h3 style='color: #2E86AB; margin: 0;'>🎙️ Third Voice</h3>
                <p style='color: #666; font-size: 0.8rem; margin: 0;'>AI Relationship Helper</p>
            </div>
            """, unsafe_allow_html=True)
            
            # User info section
            user_email = auth_manager.get_current_user_email()
            if user_email:
                st.markdown(f"""
                <div style='background: #f8f9fa; padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem;'>
                    <div style='font-size: 0.9rem; color: #666;'>👤 Signed in as:</div>
                    <div style='font-weight: bold; color: #2E86AB;'>{user_email}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Contacts section
            if contacts:
                st.markdown("### 👥 Your Contacts")
                
                # Contact list with selection
                contact_options = []
                contact_values = []
                
                for contact in contacts:
                    context_enum = RelationshipContext(contact.context)
                    display_name = f"{context_enum.emoji} {contact.name}"
                    contact_options.append(display_name)
                    contact_values.append(contact)
                
                # Current selection
                current_index = 0
                if current_contact:
                    try:
                        current_index = next(i for i, c in enumerate(contact_values) if c.id == current_contact.id)
                    except StopIteration:
                        current_index = 0
                
                selected_index = st.selectbox(
                    "Switch to:",
                    range(len(contact_options)),
                    format_func=lambda x: contact_options[x],
                    index=current_index,
                    key="sidebar_contact_selector"
                )
                
                selected_contact = contact_values[selected_index]
                
                # Update session state if selection changed
                if not current_contact or selected_contact.id != current_contact.id:
                    st.session_state.selected_contact = selected_contact
                    st.rerun()
                
                # Quick stats for current contact
                if current_contact and db and user_id:
                    messages = db.get_conversation_history(current_contact.id, user_id)
                    if messages:
                        avg_score = sum(m.healing_score for m in messages if m.healing_score) / len([m for m in messages if m.healing_score])
                        st.markdown(f"""
                        <div style='background: #e8f5e8; padding: 0.5rem; border-radius: 6px; margin: 0.5rem 0; font-size: 0.8rem;'>
                            📊 <strong>{len(messages)}</strong> conversations<br>
                            ⭐ <strong>{avg_score:.1f}/10</strong> avg healing score
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add new contact button
                if st.button("➕ Add New Contact", use_container_width=True, key="sidebar_add_contact"):
                    st.session_state.show_add_contact = True
                    st.rerun()
                
                st.markdown("---")
            
            # Quick actions section
            st.markdown("### ⚡ Quick Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💬", help="Transform Message", use_container_width=True):
                    st.session_state.quick_action = "transform"
                    st.rerun()
            
            with col2:
                if st.button("🤔", help="Interpret Message", use_container_width=True):
                    st.session_state.quick_action = "interpret"
                    st.rerun()
            
            st.markdown("---")
            
            # Help section
            with st.expander("❓ How It Works"):
                st.markdown("""
                **Transform Mode** 💬  
                Turn harsh words into healing messages
                
                **Interpret Mode** 🤔  
                Understand what they really mean
                
                **Tips:**
                - Be specific about the situation
                - Include context about your relationship
                - The AI considers your relationship type
                """)
            
            # Feedback section
            with st.expander("💭 Send Feedback"):
                feedback_text = st.text_area(
                    "Help us improve:",
                    placeholder="What features would you like to see?",
                    key="sidebar_feedback",
                    height=80
                )
                
                if st.button("Send", key="send_sidebar_feedback"):
                    if feedback_text.strip() and db and user_id:
                        if db.save_feedback(user_id, 5, feedback_text, "sidebar"):
                            st.success("Thanks for your feedback!")
                            st.session_state.sidebar_feedback = ""
                            st.rerun()
            
            st.markdown("---")
            
            # Sign out section
            st.markdown("### 🚪 Account")
            
            if st.button("🔄 Refresh Session", help="Refresh your login session", use_container_width=True):
                if auth_manager.refresh_user_data():
                    st.success("Session refreshed!")
                else:
                    st.error("Please sign in again")
                st.rerun()
            
            if st.button("🚪 Sign Out", use_container_width=True, type="secondary", key="sidebar_logout"):
                auth_manager.sign_out()
                st.rerun()
            
            # Footer
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; font-size: 0.7rem; color: #999;'>
                The Third Voice AI<br>
                Healing relationships through better communication
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_relationship_selector() -> Tuple[str, str]:
        """Render relationship context selector"""
        st.subheader("👥 Who do you need help communicating with?")
        
        # Create options
        options = []
        values = []
        for context in RelationshipContext:
            options.append(f"{context.emoji} {context.description}")
            values.append(context.value)
        
        selected_idx = st.selectbox(
            "Relationship type:",
            range(len(options)),
            format_func=lambda x: options[x],
            key="relationship_selector"
        )
        
        return values[selected_idx], options[selected_idx]
    
    @staticmethod
    def render_healing_score(score: int):
        """Render healing score visualization"""
        # Create stars based on score (1-10 scale to 1-5 stars)
        stars = "⭐" * min(5, max(1, score // 2))
        color = "#4CAF50" if score >= 7 else "#FF9800" if score >= 4 else "#F44336"
        
        st.markdown(f"""
        <div style='background: {color}20; padding: 0.5rem; border-radius: 8px; text-align: center;'>
            <strong>Healing Score: {score}/10</strong><br>
            {stars}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_feedback_form(feature_context: str) -> Optional[Tuple[int, str]]:
        """Render feedback form"""
        with st.expander("💬 How was this helpful?"):
            rating = st.slider("Rating", 1, 5, 3, key=f"rating_{feature_context}")
            feedback_text = st.text_area(
                "What could be better?", 
                placeholder="Your feedback helps us improve...",
                key=f"feedback_{feature_context}"
            )
            
            if st.button("Submit Feedback", key=f"submit_{feature_context}"):
                return rating, feedback_text
        return None
    
    @staticmethod
    def render_message_history(messages: List[Message]):
        """Render conversation history"""
        if not messages:
            st.info("No previous messages yet")
            return
        
        st.subheader("📝 Recent Conversations")
        
        for msg in messages[:5]:  # Show last 5 messages
            with st.expander(f"{msg.type.title()} - {msg.created_at.strftime('%m/%d %H:%M')}"):
                st.write("**Original:**")
                st.write(msg.original)
                
                if msg.result:
                    st.write("**AI Suggestion:**")
                    st.write(msg.result)
                    
                    if msg.healing_score:
                        UIComponents.render_healing_score(msg.healing_score)
    
    @staticmethod
    def render_logout_sidebar(auth_manager):
        """Render logout button in sidebar"""
        with st.sidebar:
            st.markdown("---")
            
            # User info
            user_email = auth_manager.get_current_user_email()
            if user_email:
                st.markdown(f"**👤 {user_email}**")
            
            # Logout button
            if st.button("🚪 Sign Out", use_container_width=True, key="sidebar_logout"):
                auth_manager.sign_out()
                st.rerun()
            
            st.markdown("---")
            st.markdown("*Need help? Contact support*")
    
    @staticmethod
    def load_custom_css():
        """Load custom CSS for mobile optimization"""
        
        st.markdown("""
        <style>
        /* Mobile-first responsive design */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Sidebar styling */
        .css-1d391kg {
            padding-top: 1rem;
        }
        
        /* Mobile optimization */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            /* Make buttons more touch-friendly */
            .stButton > button {
                height: 3rem;
                font-size: 1.1rem;
            }
            
            /* Optimize text areas for mobile */
            .stTextArea > div > div > textarea {
                font-size: 1rem;
            }
            
            /* Responsive columns */
            .row-widget.stRadio > div {
                flex-direction: column;
            }
        }
        
        /* Custom styling */
        .stSelectbox > div > div {
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #2E86AB;
            box-shadow: 0 0 0 0.2rem rgba(46, 134, 171, 0.25);
        }
        
        /* Healing score styling */
        .metric-container {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Success message styling */
        .stSuccess {
            border-radius: 8px;
        }
        
        /* Warning message styling */
        .stWarning {
            border-radius: 8px;
        }
        
        /* Error message styling */
        .stError {
            border-radius: 8px;
        }
        
        /* Logout button styling */
        .stButton[data-testid="logout_header"] > button,
        .stButton[data-testid="sidebar_logout"] > button {
            background-color: #dc3545;
            color: white;
            border: none;
        }
        
        .stButton[data-testid="logout_header"] > button:hover,
        .stButton[data-testid="sidebar_logout"] > button:hover {
            background-color: #c82333;
        }
        
        /* Sidebar quick action buttons */
        .stButton[data-testid="Transform Message"] > button {
            background-color: #28a745;
            color: white;
            padding: 0.5rem;
            font-size: 1.2rem;
        }
        
        .stButton[data-testid="Interpret Message"] > button {
            background-color: #17a2b8;
            color: white;
            padding: 0.5rem;
            font-size: 1.2rem;
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_contact_header(contact, context_enum):
        """Render contact header with emoji and description"""
        context_emoji = context_enum.emoji
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <h3 style='margin: 0; color: #2E86AB;'>{context_emoji} {contact.name}</h3>
            <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                {context_enum.description}
            </p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_ai_response(ai_response, message_type):
        """Render AI response with proper formatting"""
        from ..core.ai_engine import MessageType
        
        # Display results header
        if message_type == MessageType.TRANSFORM.value:
            st.success("🌟 Here's how to say it with love:")
        else:
            st.success("🎯 Here's what they really mean and how to respond:")
        
        # Main response
        st.markdown(f"""
        <div style='background: #f0f8ff; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #2E86AB; margin: 1rem 0;'>
            <h4 style='margin-top: 0; color: #2E86AB;'>💬 Suggested Message:</h4>
            <p style='margin-bottom: 0; font-size: 1.1rem; line-height: 1.6;'>{ai_response.transformed_message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Healing score
        UIComponents.render_healing_score(ai_response.healing_score)
        
        # Additional insights
        col1, col2 = st.columns(2)
        
        with col1:
            if ai_response.explanation:
                with st.expander("💡 Why this works better"):
                    st.write(ai_response.explanation)
        
        with col2:
            if ai_response.emotional_state != "unclear":
                with st.expander(f"😊 Emotional tone: {ai_response.emotional_state}"):
                    st.write(f"The overall emotional tone detected: **{ai_response.emotional_state}**")
        
        # Interpret mode specific insights
        if message_type == MessageType.INTERPRET.value:
            if ai_response.subtext:
                with st.expander("🎯 What they're really feeling"):
                    st.write(ai_response.subtext)
            
            if ai_response.needs:
                with st.expander("💚 Their underlying needs"):
                    for need in ai_response.needs:
                        st.write(f"• {need.title()}")
            
            if ai_response.warnings:
                with st.expander("⚠️ Things to be aware of"):
                    for warning in ai_response.warnings:
                        st.warning(warning)