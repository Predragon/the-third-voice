from supabase import create_client, Client
from typing import Optional, Dict, Any
import streamlit as st
from . import get_logger

class DataManager:
    def __init__(self, config, auth_manager):
        self.supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        self.config = config
        self.auth_manager = auth_manager
        self.ai_processor = None  # To be set externally if needed
        self.logger = get_logger("data_manager")

    def load_contacts_and_history(self) -> Dict[str, Any]:
        """Load contacts and their conversation history from database"""
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            self.logger.warning("No user ID available for loading contacts")
            return {}
        
        try:
            # Load contacts
            contacts_response = self.supabase.table("contacts").select("*").eq("user_id", user_id).execute()
            
            contacts_data = {}
            for contact in contacts_response.data:
                contacts_data[contact["name"]] = {
                    "id": contact["id"],
                    "context": contact["context"], 
                    "created_at": contact["created_at"],
                    "history": []
                }
            
            # Load messages for all contacts
            messages_response = self.supabase.table("messages").select("*").eq("user_id", user_id).order("created_at").execute()
            
            for msg in messages_response.data:
                if msg["contact_name"] in contacts_data:
                    # Import here to avoid circular imports
                    from .utils import get_current_timestamp
                    
                    contacts_data[msg["contact_name"]]["history"].append({
                        "id": msg["id"],
                        "time": get_current_timestamp(),
                        "type": msg["type"],
                        "original": msg["original"],
                        "result": msg["result"],
                        "healing_score": msg.get("healing_score", 0),
                        "model": msg.get("model", "Unknown"),
                        "sentiment": msg.get("sentiment", "unknown"),
                        "emotional_state": msg.get("emotional_state", "unknown")
                    })
            
            self.logger.info(f"Loaded {len(contacts_data)} contacts with conversation history")
            return contacts_data
            
        except Exception as e:
            self.logger.error(f"Failed to load contacts and history: {e}")
            # Import here to avoid circular imports
            from .ui.components import display_error
            display_error("Could not load data. Please try again.")
            return {}

    def save_contact(self, name: str, context: str, contact_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Save or update a contact"""
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not name.strip():
            from .ui.components import display_error
            display_error("Cannot save contact: User not logged in or invalid input.")
            return None
        
        try:
            # Import here to avoid circular imports
            from .utils import utils, get_current_timestamp
            
            contact_data = {
                "name": utils.clean_contact_name(name),
                "context": context,
                "user_id": user_id,
                "updated_at": get_current_timestamp()
            }
            
            if contact_id:
                # Update existing contact
                response = self.supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
            else:
                # Create new contact
                contact_data["created_at"] = get_current_timestamp()
                response = self.supabase.table("contacts").insert(contact_data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved contact: {name}")
                # Clear cache to ensure fresh data
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                return response.data[0]
            else:
                self.logger.error(f"Failed to save contact: {response}")
                from .ui.components import display_error
                display_error("Failed to save contact.")
                return None
                
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                from .ui.components import display_error
                display_error(f"A contact with the name '{name}' already exists.")
            else:
                self.logger.error(f"Error saving contact: {e}")
                from .ui.components import display_error
                display_error(f"Error saving contact: {e}")
            return None

    def save_message(self, contact_id: str, contact_name: str, message_type: str, original: str, result: str, 
                     emotional_state: str, healing_score: int, model_used: str, sentiment: str) -> bool:
        """Save a message to the database"""
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            from .ui.components import display_error
            display_error("Cannot save message: User not logged in or invalid contact.")
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import get_current_timestamp
            
            data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "type": message_type,
                "original": original,
                "result": result,
                "emotional_state": emotional_state,
                "healing_score": healing_score,
                "model": model_used,
                "sentiment": sentiment,
                "user_id": user_id,
                "created_at": get_current_timestamp()
            }
            
            response = self.supabase.table("messages").insert(data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved message for contact: {contact_name}")
                # Clear cache to ensure fresh data
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                return True
            else:
                self.logger.error(f"Failed to save message: {response}")
                from .ui.components import display_error
                display_error("Failed to save message.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            from .ui.components import display_error
            display_error(f"Error saving message: {e}")
            return False

    def save_interpretation(self, contact_id: str, contact_name: str, original_message: str, interpretation: str, 
                           interpretation_score: int, model_used: str) -> bool:
        """Save an interpretation to the database"""
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            from .ui.components import display_error
            display_error("Cannot save interpretation: User not logged in or invalid contact.")
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import get_current_timestamp
            
            data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "type": "interpretation",
                "original": original_message,
                "result": interpretation,
                "healing_score": interpretation_score,
                "model": model_used,
                "sentiment": "neutral",
                "emotional_state": "calm",
                "user_id": user_id,
                "created_at": get_current_timestamp()
            }
            
            response = self.supabase.table("messages").insert(data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved interpretation for contact: {contact_name}")
                # Clear cache to ensure fresh data
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                return True
            else:
                self.logger.error(f"Failed to save interpretation: {response}")
                from .ui.components import display_error
                display_error("Failed to save interpretation.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving interpretation: {e}")
            from .ui.components import display_error
            display_error(f"Could not save interpretation: {e}")
            return False

    def get_cached_ai_response(self, contact_id: str, message_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached AI response for a message"""
        try:
            response = self.supabase.table("ai_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).execute()
            if response.data:
                self.logger.debug(f"Found cached response for contact {contact_id}")
                return response.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting cached response: {e}")
            return None

    def cache_ai_response(self, contact_id: str, message_hash: str, context: str, response: str,
                         healing_score: int, model: str, sentiment: str, emotional_state: str) -> bool:
        """Cache an AI response"""
        try:
            # Import here to avoid circular imports
            from .utils import get_current_timestamp
            
            data = {
                "contact_id": contact_id,
                "message_hash": message_hash,
                "context": context,
                "response": response,
                "healing_score": healing_score,
                "model": model,
                "sentiment": sentiment,
                "emotional_state": emotional_state,
                "created_at": get_current_timestamp()
            }
            
            response = self.supabase.table("ai_cache").insert(data).execute()
            
            if response.data:
                self.logger.debug(f"Successfully cached AI response for contact {contact_id}")
                return True
            else:
                self.logger.error(f"Failed to cache AI response: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error caching AI response: {e}")
            return False

    def clear_cache(self):
        """Clear any local caches"""
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        self.logger.info("Cleared data manager cache")

    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact and all associated messages"""
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            return False
        
        try:
            # Delete messages first
            messages_response = self.supabase.table("messages").delete().eq("contact_id", contact_id).eq("user_id", user_id).execute()
            
            # Delete contact
            contact_response = self.supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
            
            if contact_response.data:
                self.logger.info(f"Successfully deleted contact {contact_id}")
                # Clear cache to ensure fresh data
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                return True
            else:
                self.logger.error(f"Failed to delete contact: {contact_response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting contact: {e}")
            return False

# No global instance - will be created in app.py
