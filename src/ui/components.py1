"""
UI Components Module for The Third Voice AI
Reusable UI components and styling utilities
Enhanced with logout functionality and copy-to-clipboard feature
"""

import streamlit as st
from typing import List, Optional, Tuple
from ..core.ai_engine import RelationshipContext
from ..data.models import Message


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
        """Render conversation history with copy functionality"""
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
                    
                    # Add copy functionality for historical messages
                    copy_key = f"copy_history_{msg.id}"
                    success_key = f"copy_success_history_{msg.id}"
                    UIComponents.render_copy_button_with_message(
                        msg.result, copy_key, success_key
                    )
                    
                    # Handle clipboard operation
                    if st.session_state.get(f"copy_text_{copy_key}"):
                        text_to_copy = st.session_state[f"copy_text_{copy_key}"]
                        clean_text = text_to_copy.replace('"', '\\"').replace('\n', '\\n')
                        
                        st.markdown(f"""
                        <script>
                        if (navigator.clipboard && window.isSecureContext) {{
                            navigator.clipboard.writeText(`{clean_text}`);
                        }} else {{
                            const textArea = document.createElement('textarea');
                            textArea.value = `{clean_text}`;
                            textArea.style.position = 'fixed';
                            textArea.style.left = '-999999px';
                            document.body.appendChild(textArea);
                            textArea.select();
                            document.execCommand('copy');
                            textArea.remove();
                        }}
                        </script>
                        """, unsafe_allow_html=True)
                        
                        del st.session_state[f"copy_text_{copy_key}"]
                    
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
        """Load custom CSS for mobile optimization and copy functionality"""
        
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
        
        /* Copy button styling */
        .copy-button {
            background-color: #28a745 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        
        .copy-button:hover {
            background-color: #218838 !important;
            transform: translateY(-1px) !important;
        }
        
        .copy-button:active {
            transform: translateY(0) !important;
        }
        
        /* AI response container styling */
        .ai-response-container {
            position: relative;
        }
        
        .copy-success {
            background-color: #d4edda !important;
            color: #155724 !important;
            border: 1px solid #c3e6cb !important;
            padding: 0.5rem !important;
            border-radius: 8px !important;
            margin-top: 0.5rem !important;
            animation: fadeInOut 3s ease-in-out !important;
        }
        
        @keyframes fadeInOut {
            0% { opacity: 0; }
            20% { opacity: 1; }
            80% { opacity: 1; }
            100% { opacity: 0; }
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
    def render_copy_button_with_message(message_text, button_key, success_key):
        """Render a copy button with success feedback"""
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("📋 Copy", key=button_key, help="Copy to clipboard", 
                        use_container_width=True, type="secondary"):
                # Store the message to copy in session state
                st.session_state[f"copy_text_{button_key}"] = message_text
                st.session_state[success_key] = True
                st.rerun()
        
        with col2:
            if st.session_state.get(success_key, False):
                st.success("✅ Copied to clipboard! Ready to paste.")
                # Clear the success state after a moment
                st.session_state[success_key] = False

    @staticmethod 
    def render_ai_response(ai_response, message_type):
        """Render AI response with proper formatting and copy functionality"""
        from ..core.ai_engine import MessageType
        import uuid
        
        # Generate unique keys for this response
        response_id = str(uuid.uuid4())[:8]
        copy_key = f"copy_main_{response_id}"
        success_key = f"copy_success_{response_id}"
        
        # Display results header
        if message_type == MessageType.TRANSFORM.value:
            st.success("🌟 Here's how to say it with love:")
        else:
            st.success("🎯 Here's what they really mean and how to respond:")
        
        # Main response with copy functionality
        st.markdown(f"""
        <div class="ai-response-container" style='background: #f0f8ff; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #2E86AB; margin: 1rem 0;'>
            <h4 style='margin-top: 0; color: #2E86AB;'>💬 Suggested Message:</h4>
            <p style='margin-bottom: 0; font-size: 1.1rem; line-height: 1.6;'>{ai_response.transformed_message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Copy button with enhanced styling and feedback
        UIComponents.render_copy_button_with_message(
            ai_response.transformed_message, 
            copy_key, 
            success_key
        )
        
        # Handle the actual clipboard operation using JavaScript
        if st.session_state.get(f"copy_text_{copy_key}"):
            text_to_copy = st.session_state[f"copy_text_{copy_key}"]
            # Clean the text for JavaScript
            clean_text = text_to_copy.replace('"', '\\"').replace('\n', '\\n')
            
            st.markdown(f"""
            <script>
            // Copy to clipboard
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(`{clean_text}`).then(function() {{
                    console.log('Text copied to clipboard');
                }}).catch(function(err) {{
                    console.error('Failed to copy text: ', err);
                }});
            }} else {{
                // Fallback for older browsers or non-HTTPS
                const textArea = document.createElement('textarea');
                textArea.value = `{clean_text}`;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    console.log('Text copied to clipboard (fallback)');
                }} catch (err) {{
                    console.error('Failed to copy text (fallback): ', err);
                }}
                textArea.remove();
            }}
            </script>
            """, unsafe_allow_html=True)
            
            # Clear the copy text from session state
            del st.session_state[f"copy_text_{copy_key}"]
        
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
        
        # Add model info (only if ai_response has the attribute)
        if hasattr(ai_response, 'model_used') and ai_response.model_used:
            st.caption(f"🤖 Powered by {ai_response.model_used}")
        elif hasattr(ai_response, 'model_display') and ai_response.model_display:
            st.caption(f"🤖 {ai_response.model_display}")
