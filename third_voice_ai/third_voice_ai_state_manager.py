from typing import Any, Dict, Optional, List
import streamlit as st

class StateManager:
    def __init__(self):
        self.init_session_state()
        
    def init_session_state(self) -> None:
        if 'authenticated' not in st.session_state:
            st.session_state.update({'authenticated': False, 'app_mode': 'login', 'active_contact': None, 
                                  'contacts': {}, 'contacts_count': 0, 'has_error': False, 'error_message': None,
                                  'conversation_input_length': 0, 'clear_conversation_input': False})

    def get(self, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        st.session_state[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        st.session_state.update(updates)

    def clear_key(self, key: str) -> None:
        if key in st.session_state:
            del st.session_state[key]

    def is_authenticated(self) -> bool:
        return self.get('authenticated', False)

    def get_contacts(self) -> Dict[str, Any]:
        return self.get('contacts', {})

    def set_contacts(self, contacts: Dict[str, Any]) -> None:
        self.set('contacts', contacts)
        self.set('contacts_count', len(contacts))

    def get_active_contact(self) -> Optional[str]:
        return self.get('active_contact')

    def set_active_contact(self, contact_name: Optional[str]) -> None:
        self.set('active_contact', contact_name)

    def get_contact_data(self, contact_name: str) -> Dict[str, Any]:
        contacts = self.get_contacts()
        return contacts.get(contact_name, {"context": "family", "history": [], "id": None})

    def set_error(self, error_message: str) -> None:
        self.set('error_message', error_message)
        self.set('has_error', True)

    def get_error(self) -> Optional[str]:
        return self.get('error_message')

    def clear_error(self) -> None:
        self.set('error_message', None)
        self.set('has_error', False)

    def get_conversation_input(self) -> str:
        return self.get('conversation_input_text', '')

    def set_conversation_input(self, text: str) -> None:
        self.set('conversation_input_text', text)

    def should_clear_input(self) -> bool:
        return self.get('clear_conversation_input', False)

    def reset_clear_flag(self) -> None:
        self.set('clear_conversation_input', False)

    def set_last_response(self, contact_name: str, response_data: Dict[str, Any]) -> None:
        self.set(f"last_response_{contact_name}", response_data)

    def get_last_response(self, contact_name: str) -> Optional[Dict[str, Any]]:
        return self.get(f"last_response_{contact_name}")

    def clear_last_response(self, contact_name: str) -> None:
        self.clear_key(f"last_response_{contact_name}")

    def set_last_interpretation(self, contact_name: str, interpretation_data: Dict[str, Any]) -> None:
        self.set(f"last_interpretation_{contact_name}", interpretation_data)

    def get_last_interpretation(self, contact_name: str) -> Optional[Dict[str, Any]]:
        return self.get(f"last_interpretation_{contact_name}")

    def clear_last_interpretation(self, contact_name: str) -> None:
        self.clear_key(f"last_interpretation_{contact_name}")