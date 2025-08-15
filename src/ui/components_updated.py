"""
UI Components Module for The Third Voice AI
Reusable UI components and styling utilities
Optimized for friction-free demo experience
"""

import streamlit as st
from typing import List, Optional, Tuple
from ..core.ai_engine import RelationshipContext
from ..data.models import Message


class UIComponents:
    """Reusable UI components optimized for demo experience"""
    
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
    def render_clean_demo_header(auth_manager):
        """Render clean demo header without clutter"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("""
            <div style='padding: 0.5rem 0;'>
                <h2 style='color: #2E86AB; margin: 0; display: inline-flex; align-items: center;'>
                    🎭 Third Voice Demo
                </h2>
                <p style='color: #666; font-size: 0.9rem; margin: 0;'>
                    Experience AI-powered communication healing
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Simple demo status
            stats = auth_manager.get_demo_stats()
            messages_count = stats.get('messages', 0)
            
            if messages_count > 0:
                st.markdown(f"""
                <div style='text-align: right; padding: 0.2rem 0; font-size: 0.8rem; color: #666;'>
                    🎯 {messages_count} messages tried
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚪 Exit Demo", key="demo_logout", help="Exit demo mode"):
                auth_manager.sign_out()
                st.rerun()
    
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
                    
                    # Add copy functionality
                    copy_key = f"copy_history_{msg.id}"
                    success_key = f"copy_success_history_{msg.id}"
                    UIComponents.render_copy_button_with_message(
                        msg.result, copy_key, success_key
                    )
                    
                    if msg.healing_score:
                        UIComponents.render_healing_score(msg.healing_score)
    
    @staticmethod
    def render_logout_sidebar(auth_manager):
        """Render logout button in sidebar"""
        with st.sidebar:
            st.markdown("---")
            
            user_email = auth_manager.get_current_user_email()
            if user_email:
                st.markdown(f"**👤 {user_email}**")
            
            if st.button("🚪 Sign Out", use_container_width=True, key="sidebar_logout"):
                auth_manager.sign_out()
                st.rerun()
            
            st.markdown("---")
            st.markdown("*Need help? Contact support*")
    
    @staticmethod
    def load_custom_css():
        """Load custom CSS for mobile optimization and demo experience"""
        
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
        
        /* Demo-specific styling */
        .demo-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            text-align: center;
        }
        
        /* Enhanced button styling */
        .stButton > button[data-testid*="demo"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 1rem 2rem !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        }
        
        .stButton > button[data-testid*="demo"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        }
        
        /* Mobile optimization */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            .stButton > button {
                height: 3rem;
                font-size: 1.1rem;
            }
            
            .stTextArea > div > div > textarea {
                font-size: 1rem;
            }
            
            .demo-gradient {
                padding: 1.5rem 1rem;
                font-size: 0.9rem;
            }
        }
        
        /* Form styling */
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
        
        /* Success animations */
        .copy-success {
            background-color: #d4edda !important;
            color: #155724 !important;
            border: 1px solid #c3e6cb !important;
            padding: 0.5rem !important;
            border-radius: 8px !important;
            margin-top: 0.5rem !important;
            animation: slideIn 0.3s ease-in !important;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Clean demo interface */
        .demo-clean {
            background: rgba(102, 126, 234, 0.05);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
        }
        
        .demo-mode-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #2E86AB;
            margin-bottom: 1rem;
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
                st.session_state[f"copy_text_{button_key}"] = message_text
                st.session_state[success_key] = True
                st.rerun()
        
        with col2:
            if st.session_state.get(success_key, False):
                st.success("✅ Copied to clipboard! Ready to paste.")
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
            clean_text = text_to_copy.replace('"', '\\"').replace('\n', '\\n')
            
            st.markdown(f"""
            <script>
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(`{clean_text}`).then(function() {{
                    console.log('Text copied to clipboard');
                }}).catch(function(err) {{
                    console.error('Failed to copy text: ', err);
                }});
            }} else {{
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
        
        # Add model info
        if hasattr(ai_response, 'model_used') and ai_response.model_used:
            st.caption(f"🤖 Powered by {ai_response.model_used}")
        elif hasattr(ai_response, 'model_display') and ai_response.model_display:
            st.caption(f"🤖 {ai_response.model_display}")

    @staticmethod
    def render_demo_ai_response(ai_response, message_type):
        """Render AI response optimized for demo users with enhanced visual appeal"""
        from ..core.ai_engine import MessageType
        import uuid
        
        response_id = str(uuid.uuid4())[:8]
        copy_key = f"copy_demo_{response_id}"
        success_key = f"copy_success_demo_{response_id}"
        
        # Enhanced demo results header with animation
        if message_type == MessageType.TRANSFORM.value:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                        color: white; padding: 1.5rem; border-radius: 16px; margin: 1rem 0; text-align: center;
                        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3); animation: slideInUp 0.5s ease-out;'>
                <h3 style='margin: 0; color: white; display: inline-flex; align-items: center; gap: 0.5rem;'>
                    ✨ Transformed with Love!
                </h3>
            </div>
            
            <style>
            @keyframes slideInUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            </style>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); 
                        color: white; padding: 1.5rem; border-radius: 16px; margin: 1rem 0; text-align: center;
                        box-shadow: 0 4px 20px rgba(255, 152, 0, 0.3); animation: slideInUp 0.5s ease-out;'>
                <h3 style='margin: 0; color: white; display: inline-flex; align-items: center; gap: 0.5rem;'>
                    🎯 Hidden Meaning Revealed!
                </h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Main response with enhanced demo styling
        st.markdown(f"""
        <div class="demo-mode-card" style='background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%); 
                                            padding: 2rem; border-radius: 16px; border-left: 6px solid #2E86AB; 
                                            margin: 1.5rem 0; box-shadow: 0 6px 25px rgba(46, 134, 171, 0.15);'>
            <h4 style='margin-top: 0; color: #2E86AB; font-size: 1.2rem; display: inline-flex; align-items: center; gap: 0.5rem;'>
                💬 Your AI-Suggested Message:
            </h4>
            <div style='background: white; padding: 1.5rem; border-radius: 12px; margin-top: 1rem; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid rgba(46, 134, 171, 0.1);'>
                <p style='margin: 0; font-size: 1.1rem; line-height: 1.7; color: #333;'>
                    {ai_response.transformed_message}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced copy button for demo
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("📋 Copy Message", 
                        key=copy_key, 
                        help="Copy this message to use in your conversation!", 
                        use_container_width=True, 
                        type="primary"):
                st.session_state[f"copy_text_{copy_key}"] = ai_response.transformed_message
                st.balloons()  # Fun demo feedback
                st.success("✅ Copied! Ready to paste into your message app!")
        
        with col2:
            # Demo encouragement
            st.markdown("""
            <div style='background: #e8f5e8; padding: 1rem; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                <p style='margin: 0; color: #2d5016; font-size: 0.95rem;'>
                    💡 <strong>Try it!</strong> Copy this message and see how it transforms your conversation.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Handle clipboard with enhanced demo feedback
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
        
        # Enhanced healing score for demo
        score_color = "#4CAF50" if ai_response.healing_score >= 7 else "#FF9800" if ai_response.healing_score >= 4 else "#F44336"
        stars = "⭐" * min(5, max(1, ai_response.healing_score // 2))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {score_color} 0%, {score_color}cc 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; text-align: center; margin: 1rem 0;
                    box-shadow: 0 4px 15px {score_color}33;'>
            <h4 style='margin: 0 0 0.5rem 0; color: white;'>Healing Potential</h4>
            <div style='font-size: 1.5rem; margin: 0.5rem 0;'>{stars}</div>
            <div style='font-size: 1.2rem; font-weight: bold;'>{ai_response.healing_score}/10</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo-specific insights (more engaging)
        if ai_response.explanation or (message_type == MessageType.INTERPRET.value and ai_response.subtext):
            st.markdown("---")
            st.markdown("### 🧠 Why This Works")
            
            if ai_response.explanation:
                st.markdown(f"""
                <div style='background: #fff8e1; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #FFC107; margin: 1rem 0;'>
                    <h5 style='margin: 0 0 1rem 0; color: #F57C00; display: inline-flex; align-items: center; gap: 0.5rem;'>
                        💡 The Psychology Behind It:
                    </h5>
                    <p style='margin: 0; line-height: 1.6; color: #5d4037;'>{ai_response.explanation}</p>
                </div>
                """, unsafe_allow_html=True)
            
            if message_type == MessageType.INTERPRET.value and ai_response.subtext:
                st.markdown(f"""
                <div style='background: #f3e5f5; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #9C27B0; margin: 1rem 0;'>
                    <h5 style='margin: 0 0 1rem 0; color: #7B1FA2; display: inline-flex; align-items: center; gap: 0.5rem;'>
                        🎯 What They're Really Saying:
                    </h5>
                    <p style='margin: 0; line-height: 1.6; color: #4a148c;'>{ai_response.subtext}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Demo model attribution
        st.caption("🎭 Demo powered by The Third Voice AI")

    @staticmethod
    def render_demo_success_celebration():
        """Render success celebration for demo users"""
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                    color: white; padding: 2rem; border-radius: 16px; margin: 2rem 0; text-align: center;
                    box-shadow: 0 6px 30px rgba(76, 175, 80, 0.3); animation: celebration 1s ease-out;'>
            <h2 style='margin: 0 0 1rem 0; color: white;'>🎉 Amazing! You're Getting Great Results!</h2>
            <p style='margin: 0 0 1.5rem 0; opacity: 0.95; font-size: 1.1rem;'>
                See how AI can transform your relationships? Keep your progress forever with a free account!
            </p>
        </div>
        
        <style>
        @keyframes celebration {
            0% { transform: scale(0.8); opacity: 0; }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); opacity: 1; }
        }
        </style>
        """, unsafe_allow_html=True)
                