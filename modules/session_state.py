"""
Session state management for The Third Voice AI
Keeping track of the user's journey and data
"""

import streamlit as st
from .config import REQUIRE_TOKEN

def initialize_session_state():
    """Initialize all session state variables with defaults"""
    
    # Default session state values
    defaults = {
        # Authentication
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
        
        # Core data structures
        'contacts': {
            'General': {
                'context': 'general',
                'history': []
            }
        },
        'active_contact': 'General',
        'journal_entries': {},
        'feedback_data': {},
        
        # User statistics
        'user_stats': {
            'total_messages': 0,
            'coached_messages': 0,
            'translated_messages': 0
        },
        
        # UI state
        'active_mode': None,  # 'coach' or 'translate'
        'show_advanced': False,
        'last_save_time': None
    }
    
    # Set defaults only if not already set
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_current_contact():
    """Get the currently active contact"""
    return st.session_state.contacts[st.session_state.active_contact]

def add_contact(name: str, context: str) -> bool:
    """
    Add a new contact to the system
    
    Args:
        name: Contact name
        context: Relationship context
        
    Returns:
        True if added successfully, False if contact already exists
    """
    if name in st.session_state.contacts:
        return False
    
    st.session_state.contacts[name] = {
        'context': context,
        'history': []
    }
    st.session_state.active_contact = name
    return True

def delete_contact(name: str) -> bool:
    """
    Delete a contact (except General)
    
    Args:
        name: Contact name to delete
        
    Returns:
        True if deleted, False if it was General or didn't exist
    """
    if name == "General" or name not in st.session_state.contacts:
        return False
    
    del st.session_state.contacts[name]
    
    # Switch to General if we deleted the active contact
    if st.session_state.active_contact == name:
        st.session_state.active_contact = "General"
    
    return True

def add_history_entry(contact_name: str, entry: dict):
    """
    Add a history entry to a specific contact
    
    Args:
        contact_name: Name of the contact
        entry: Dictionary containing the history entry
    """
    if contact_name in st.session_state.contacts:
        st.session_state.contacts[contact_name]['history'].append(entry)

def update_user_stats(stat_type: str):
    """
    Update user statistics
    
    Args:
        stat_type: Type of stat to increment ('total_messages', 'coached_messages', 'translated_messages')
    """
    if stat_type in st.session_state.user_stats:
        st.session_state.user_stats[stat_type] += 1

def set_feedback(entry_id: str, feedback_type: str):
    """
    Set feedback for a specific entry
    
    Args:
        entry_id: Unique identifier for the entry
        feedback_type: Type of feedback ('positive', 'neutral', 'negative')
    """
    st.session_state.feedback_data[entry_id] = feedback_type

def get_contact_stats(contact_name: str) -> dict:
    """
    Get statistics for a specific contact
    
    Args:
        contact_name: Name of the contact
        
    Returns:
        Dictionary with contact statistics
    """
    if contact_name not in st.session_state.contacts:
        return {'total': 0, 'coached': 0, 'translated': 0}
    
    history = st.session_state.contacts[contact_name]['history']
    
    return {
        'total': len(history),
        'coached': sum(1 for h in history if h['type'] == 'coach'),
        'translated': sum(1 for h in history if h['type'] == 'translate')
    }

def get_feedback_stats() -> dict:
    """
    Get overall feedback statistics
    
    Returns:
        Dictionary with feedback counts
    """
    feedback_counts = {
        'positive': 0,
        'neutral': 0,  
        'negative': 0
    }
    
    for feedback in st.session_state.feedback_data.values():
        if feedback in feedback_counts:
            feedback_counts[feedback] += 1
    
    return feedback_counts

def clear_session_data():
    """Clear all session data (for fresh start)"""
    keys_to_clear = [
        'contacts', 'active_contact', 'journal_entries', 
        'feedback_data', 'user_stats', 'active_mode'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Reinitialize with defaults
    initialize_session_state()

def export_session_data() -> dict:
    """
    Export session data for saving
    
    Returns:
        Dictionary containing all exportable session data
    """
    import datetime
    
    return {
        'contacts': st.session_state.contacts,
        'journal_entries': st.session_state.journal_entries,
        'feedback_data': st.session_state.feedback_data,
        'user_stats': st.session_state.user_stats,
        'exported_at': datetime.datetime.now().isoformat(),
        'version': '1.0.0'
    }

def import_session_data(data: dict) -> bool:
    """
    Import session data from saved file
    
    Args:
        data: Dictionary containing session data
        
    Returns:
        True if import successful, False otherwise
    """
    try:
        # Validate required keys exist
        required_keys = ['contacts', 'journal_entries', 'feedback_data', 'user_stats']
        if not all(key in data for key in required_keys):
            return False
        
        # Import the data
        st.session_state.contacts = data.get('contacts', {'General': {'context': 'general', 'history': []}})
        st.session_state.journal_entries = data.get('journal_entries', {})
        st.session_state.feedback_data = data.get('feedback_data', {})
        st.session_state.user_stats = data.get('user_stats', {
            'total_messages': 0,
            'coached_messages': 0,
            'translated_messages': 0
        })
        
        # Ensure active contact is valid
        if st.session_state.active_contact not in st.session_state.contacts:
            st.session_state.active_contact = "General"
        
        return True
        
    except Exception as e:
        st.error(f"Import failed: {str(e)}")
        return False
