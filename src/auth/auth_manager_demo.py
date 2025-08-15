"""
Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
Enhanced with session persistence and demo login functionality
"""

import streamlit as st
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta


class AuthManager:
    """Handle authentication workflows"""
    
    # Demo user credentials
    DEMO_USERS = {
        "demo@thethirdvoice.ai": {
            "password": "demo123",
            "name": "Demo User",
            "id": "demo-user-001"
        },
        "guest@thethirdvoice.ai": {
            "password": "guest123", 
            "name": "Guest User",
            "id": "demo-user-002"
        }
    }
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        # Check for existing session on initialization
        self._check_existing_session()
    
    def _check_existing_session(self):
        """Check if there's an existing Supabase session or demo session"""
        try:
            # Check for demo session first
            if st.session_state.get('is_demo_user', False):
                return  # Demo session already active
                
            # Get current session from Supabase
            session = self.supabase.auth.get_session()
            if session and session.user:
                # Store user in session state if not already there
                if not hasattr(st.session_state, 'user') or st.session_state.user is None:
                    st.session_state.user = session.user
                    print(f"✅ Restored session for user: {session.user.email}")
        except Exception as e:
            print(f"⚠️ Could not check existing session: {str(e)}")
    
    def sign_up(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user"""
        # Check if trying to sign up with demo credentials
        if email in self.DEMO_USERS:
            return False, "Demo accounts cannot be registered. Please use different email."
            
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                return True, "Check your email for verification link!"
            else:
                return False, "Sign up failed"
                
        except Exception as e:
            return False, f"Sign up error: {str(e)}"
    
    def sign_in(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign in user (regular or demo)"""
        # Check if it's a demo login
        if email in self.DEMO_USERS:
            return self._sign_in_demo(email, password)
        
        # Regular Supabase login
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                st.session_state.user = response.user
                st.session_state.is_demo_user = False
                return True, "Successfully signed in!"
            else:
                return False, "Invalid credentials"
                
        except Exception as e:
            return False, f"Sign in error: {str(e)}"
    
    def _sign_in_demo(self, email: str, password: str) -> Tuple[bool, str]:
        """Handle demo user sign in"""
        demo_user = self.DEMO_USERS.get(email)
        
        if not demo_user or demo_user["password"] != password:
            return False, "Invalid demo credentials"
        
        # Create mock user object for demo
        class MockUser:
            def __init__(self, user_data):
                self.id = user_data["id"] 
                self.email = email
                self.user_metadata = {"name": user_data["name"]}
        
        # Set up demo session
        st.session_state.user = MockUser(demo_user)
        st.session_state.is_demo_user = True
        st.session_state.demo_start_time = datetime.now()
        
        # Log demo usage (optional analytics)
        self._log_demo_usage(email)
        
        return True, f"Welcome to the demo, {demo_user['name']}! 🎭"
    
    def _log_demo_usage(self, email: str):
        """Log demo usage for analytics"""
        try:
            # Get user's IP (Streamlit doesn't expose this directly, but we can try)
            user_ip = st.session_state.get('user_ip', 'unknown')
            
            # Insert into demo_usage table
            self.supabase.table("demo_usage").insert({
                "user_email": email,
                "login_time": datetime.now().isoformat(),
                "ip_address": user_ip
            }).execute()
            
            print(f"📊 Demo usage logged for {email}")
        except Exception as e:
            print(f"⚠️ Could not log demo usage: {str(e)}")
    
    def sign_out(self):
        """Sign out user (regular or demo)"""
        try:
            # Clear demo session data
            if st.session_state.get('is_demo_user', False):
                print("✅ Demo user signed out")
            else:
                # Regular Supabase sign out
                self.supabase.auth.sign_out()
                print("✅ User signed out successfully")
                
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
                
        except Exception as e:
            st.error(f"Sign out error: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (regular or demo)"""
        # Check demo session first
        if st.session_state.get('is_demo_user', False):
            # Check if demo session is still valid (optional: add time limit)
            demo_start = st.session_state.get('demo_start_time')
            if demo_start and datetime.now() - demo_start > timedelta(hours=2):
                # Demo session expired
                self.sign_out()
                return False
            return True
        
        # Check regular session state
        if hasattr(st.session_state, 'user') and st.session_state.user is not None:
            return True
        
        # If not in session state, check Supabase session
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                st.session_state.is_demo_user = False
                return True
        except:
            pass
        
        return False
    
    def is_demo_user(self) -> bool:
        """Check if current user is a demo user"""
        return st.session_state.get('is_demo_user', False)
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.is_authenticated():
            return st.session_state.user.id
        return None
    
    def get_current_user_email(self) -> Optional[str]:
        """Get current user email"""
        if self.is_authenticated():
            return st.session_state.user.email
        return None
    
    def get_demo_time_remaining(self) -> Optional[str]:
        """Get remaining demo time (if applicable)"""
        if not self.is_demo_user():
            return None
            
        demo_start = st.session_state.get('demo_start_time')
        if not demo_start:
            return None
            
        elapsed = datetime.now() - demo_start
        remaining = timedelta(hours=2) - elapsed
        
        if remaining.total_seconds() <= 0:
            return "Expired"
            
        hours = int(remaining.seconds // 3600)
        minutes = int((remaining.seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"