# state_manager.py - The Third Voice AI State Management
# Centralized session state management for Streamlit

import streamlit as st
from typing import Any, Dict, Optional, List
from .config import DEFAULT_SESSION_STATE, CONTEXTS

class StateManager:
    """
    Centralized state management for The Third Voice AI
    Handles all session state operations with mobile-friendly error handling
    """
    
    def __init__(self):
        """Initialize state manager and ensure default values are set"""
        self.init_session_state()
        
    def init_session_state(self) -> None:
        """Initialize session state with default values"""
        for key, value in DEFAULT_SESSION_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from session state with fallback
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in session state
        
        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple session state values
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
        for key, value in updates.items():
            st.session_state[key] = value
    
    def clear_key(self, key: str) -> None:
        """
        Clear a specific key from session state
        
        Args:
            key: Session state key to clear
        """
        if key in st.session_state:
            del st.session_state[key]
    
    def clear_multiple(self, keys: List[str]) -> None:
        """
        Clear multiple keys from session state
        
        Args:
            keys: List of session state keys to clear
        """
        for key in keys:
            self.clear_key(key)
    
    def reset_to_defaults(self, exclude: Optional[List[str]] = None) -> None:
        """
        Reset session state to default values
        
        Args:
            exclude: List of keys to exclude from reset
        """
        exclude = exclude or []
        for key, value in DEFAULT_SESSION_STATE.items():
            if key not in exclude:
                st.session_state[key] = value
    
    # Authentication State Management
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get('authenticated', False)
    
    def get_user(self) -> Optional[Any]:
        """Get current user object"""
        return self.get('user')
    
    def set_authenticated(self, user: Any) -> None:
        """Set authentication state"""
        self.update({
            'authenticated': True,
            'user': user
        })
    
    def clear_authentication(self) -> None:
        """Clear authentication state"""
        self.update({
            'authenticated': False,
            'user': None,
            'app_mode': 'login'
        })
    
    # App Mode Management
    def get_app_mode(self) -> str:
        """Get current app mode"""
        return self.get('app_mode', 'login')
    
    def set_app_mode(self, mode: str) -> None:
        """Set app mode"""
        self.set('app_mode', mode)
    
    def navigate_to(self, mode: str, **kwargs) -> None:
        """
        Navigate to a specific app mode with optional state updates
        
        Args:
            mode: App mode to navigate to
            **kwargs: Additional state updates
        """
        updates = {'app_mode': mode}
        updates.update(kwargs)
        self.update(updates)
    
    # Contact Management
    def get_contacts(self) -> Dict[str, Any]:
        """Get all contacts"""
        return self.get('contacts', {})
    
    def set_contacts(self, contacts: Dict[str, Any]) -> None:
        """Set contacts dictionary"""
        self.set('contacts', contacts)
    
    def get_active_contact(self) -> Optional[str]:
        """Get active contact name"""
        return self.get('active_contact')
    
    def set_active_contact(self, contact_name: Optional[str]) -> None:
        """Set active contact"""
        self.set('active_contact', contact_name)
    
    def get_contact_data(self, contact_name: str) -> Dict[str, Any]:
        """
        Get data for a specific contact
        
        Args:
            contact_name: Name of the contact
            
        Returns:
            Contact data dictionary with defaults
        """
        contacts = self.get_contacts()
        return contacts.get(contact_name, {
            "context": "family", 
            "history": [], 
            "id": None
        })
    
    # Error Management
    def set_error(self, error_message: str) -> None:
        """Set error message"""
        self.set('last_error_message', error_message)
    
    def get_error(self) -> Optional[str]:
        """Get current error message"""
        return self.get('last_error_message')
    
    def clear_error(self) -> None:
        """Clear error message"""
        self.clear_key('last_error_message')
    
    # Input Management
    def get_conversation_input(self) -> str:
        """Get conversation input text"""
        return self.get('conversation_input_text', '')
    
    def set_conversation_input(self, text: str) -> None:
        """Set conversation input text"""
        self.set('conversation_input_text', text)
    
    def clear_conversation_input(self) -> None:
        """Clear conversation input"""
        self.update({
            'conversation_input_text': '',
            'clear_conversation_input': True
        })
    
    def should_clear_input(self) -> bool:
        """Check if input should be cleared"""
        return self.get('clear_conversation_input', False)
    
    def reset_clear_flag(self) -> None:
        """Reset the clear input flag"""
        self.set('clear_conversation_input', False)
    
    # Verification Management
    def set_verification_notice(self, email: str) -> None:
        """Set verification notice state"""
        self.update({
            'show_verification_notice': True,
            'verification_email': email,
            'app_mode': 'verification_notice'
        })
    
    def clear_verification_notice(self) -> None:
        """Clear verification notice state"""
        self.update({
            'show_verification_notice': False,
            'verification_email': None
        })
    
    # Response Management
    def set_last_response(self, contact_name: str, response_data: Dict[str, Any]) -> None:
        """
        Set last AI response for a contact
        
        Args:
            contact_name: Name of the contact
            response_data: Response data dictionary
        """
        self.set(f"last_response_{contact_name}", response_data)
    
    def get_last_response(self, contact_name: str) -> Optional[Dict[str, Any]]:
        """
        Get last AI response for a contact
        
        Args:
            contact_name: Name of the contact
            
        Returns:
            Response data dictionary or None
        """
        return self.get(f"last_response_{contact_name}")
    
    def clear_last_response(self, contact_name: str) -> None:
        """
        Clear last AI response for a contact
        
        Args:
            contact_name: Name of the contact
        """
        self.clear_key(f"last_response_{contact_name}")
    
    # Interpretation Management
    def set_last_interpretation(self, contact_name: str, interpretation_data: Dict[str, Any]) -> None:
        """
        Set last interpretation for a contact
        
        Args:
            contact_name: Name of the contact
            interpretation_data: Interpretation data dictionary
        """
        self.set(f"last_interpretation_{contact_name}", interpretation_data)
    
    def get_last_interpretation(self, contact_name: str) -> Optional[Dict[str, Any]]:
        """
        Get last interpretation for a contact
        
        Args:
            contact_name: Name of the contact
            
        Returns:
            Interpretation data dictionary or None
        """
        return self.get(f"last_interpretation_{contact_name}")
    
    def clear_last_interpretation(self, contact_name: str) -> None:
        """
        Clear last interpretation for a contact
        
        Args:
            contact_name: Name of the contact
        """
        self.clear_key(f"last_interpretation_{contact_name}")
    
    # Utility Methods
    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about current state
        
        Returns:
            Dictionary with debug information
        """
        return {
            "authenticated": self.is_authenticated(),
            "app_mode": self.get_app_mode(),
            "active_contact": self.get_active_contact(),
            "contacts_count": len(self.get_contacts()),
            "has_error": bool(self.get_error()),
            "conversation_input_length": len(self.get_conversation_input())
        }
    
    def refresh_data(self) -> None:
        """Trigger data refresh by clearing cached data"""
        # Clear any cached response data
        keys_to_clear = [key for key in st.session_state.keys() 
                        if key.startswith(('last_response_', 'last_interpretation_'))]
        self.clear_multiple(keys_to_clear)

# Global state manager instance
state_manager = StateManager()
