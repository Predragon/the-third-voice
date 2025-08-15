"""
Enhanced Authentication UI with Demo Login Option
"""

import streamlit as st
from typing import List, Optional, Tuple
from ..core.ai_engine import MessageType, RelationshipContext
from ..data.models import Contact, Message
from .components import UIComponents


class AuthenticationUI:
    """Authentication user interface with demo support"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
    
    def run(self) -> bool:
        """Run authentication flow, return True if authenticated"""
        
        if self.auth_manager.is_authenticated():
            return True
        
        UIComponents.render_header()
        
        # Check URL params for verification (using newer API)
        try:
            query_params = st.query_params
            if 'type' in query_params and query_params['type'] == 'signup':
                st.success("✅ Email verified! Please sign in below.")
        except:
            # Fallback for older Streamlit versions
            try:
                query_params = st.experimental_get_query_params()
                if 'type' in query_params and query_params['type'][0] == 'signup':
                    st.success("✅ Email verified! Please sign in below.")
            except:
                pass
        
        # Demo banner
        self._render_demo_banner()
        
        tab1, tab2, tab3 = st.tabs(["🎭 Try Demo", "🔑 Sign In", "📝 Sign Up"])
        
        with tab1:
            self._render_demo_tab()
        
        with tab2:
            self._render_sign_in_form()
        
        with tab3:
            self._render_sign_up_form()
        
        return False
    
    def _render_demo_banner(self):
        """Render demo information banner"""
        st.markdown("""
        <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; text-align: center;'>
            <h3 style='margin: 0; color: white;'>🎭 Try Before You Sign Up!</h3>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>
                Experience The Third Voice with our demo accounts - no email required!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_demo_tab(self):
        """Render demo login tab"""
        st.markdown("""
        ### 🎭 Demo Access
        
        Try The Third Voice instantly with pre-configured demo accounts:
        """)
        
        # Demo account options
        demo_accounts = [
            {
                "name": "👥 Family Demo",
                "email": "demo@thethirdvoice.ai", 
                "password": "demo123",
                "description": "Try with family/parenting scenarios"
            },
            {
                "name": "💼 Guest Demo", 
                "email": "guest@thethirdvoice.ai",
                "password": "guest123", 
                "description": "General relationship communication"
            }
        ]
        
        for account in demo_accounts:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **{account['name']}**  
                    {account['description']}  
                    `{account['email']}` / `{account['password']}`
                    """)
                
                with col2:
                    if st.button(f"Try {account['name']}", 
                               key=f"demo_{account['email']}", 
                               use_container_width=True):
                        self._try_demo_login(account['email'], account['password'])
                
                st.divider()
        
        # Demo features explanation
        with st.expander("ℹ️ What's included in the demo?"):
            st.markdown("""
            **Full Features Available:**
            - ✅ Transform messages to be more healing
            - ✅ Interpret what people really mean  
            - ✅ Create contacts for different relationships
            - ✅ View conversation history
            - ✅ All relationship contexts (family, romantic, workplace, etc.)
            
            **Demo Limitations:**
            - ⏰ 2-hour session limit (resets when you restart)
            - 🔄 Data resets between sessions
            - 📊 No long-term conversation history
            
            **Ready to save your progress?** Sign up for a free account!
            """)
        
        # Manual demo login form (for those who prefer typing)
        st.markdown("---")
        st.markdown("**Or enter demo credentials manually:**")
        
        with st.form("manual_demo_form"):
            email = st.text_input("Demo Email", placeholder="demo@thethirdvoice.ai")
            password = st.text_input("Demo Password", type="password", placeholder="demo123")
            
            if st.form_submit_button("🎭 Start Demo", use_container_width=True, type="primary"):
                if email and password:
                    self._try_demo_login(email, password)
                else:
                    st.error("Please enter demo credentials")
    
    def _try_demo_login(self, email: str, password: str):
        """Attempt demo login"""
        success, message = self.auth_manager.sign_in(email, password)
        if success:
            st.success(message)
            st.balloons()
            st.rerun()
        else:
            st.error(message)
    
    def _render_sign_in_form(self):
        """Render sign in form"""
        
        st.subheader("Welcome Back")
        
        # Show demo credentials hint
        st.info("💡 **Tip:** You can also use demo credentials here: `demo@thethirdvoice.ai` / `demo123`")
        
        with st.form("sign_in_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                if email and password:
                    success, message = self.auth_manager.sign_in(email, password)
                    if success:
                        st.success(message)
                        if not self.auth_manager.is_demo_user():
                            st.balloons()  # Only show balloons for real users
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    def _render_sign_up_form(self):
        """Render sign up form"""
        
        st.subheader("Create Account")
        st.markdown("Join thousands healing their relationships with AI")
        
        # Benefits of signing up vs demo
        with st.expander("🌟 Why create an account vs using demo?"):
            st.markdown("""
            **Free Account Benefits:**
            - 💾 **Save your conversations** forever
            - 📈 **Track your progress** over time
            - 👥 **Unlimited contacts** and relationships
            - 🔄 **No time limits** or session resets
            - 🎯 **Personalized insights** based on your history
            - 🔒 **Private and secure** - your data stays yours
            
            **Still completely free!** We believe healing relationships shouldn't cost money.
            """)
        
        with st.form("sign_up_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", help="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Free Account", use_container_width=True, type="primary"):
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