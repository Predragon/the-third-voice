# data_manager.py - The Third Voice AI Data Management
# Supabase database operations with mobile-friendly caching

import streamlit as st
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from . import get_logger

class DataManager:
    """
    Database manager for The Third Voice AI
    Handles all Supabase operations with intelligent caching
    """
    
    def __init__(self, config, auth_manager):
        """Initialize with Supabase client from auth manager"""
        self.config = config
        self.auth_manager = auth_manager
        self.supabase = auth_manager.supabase
        self.logger = get_logger("data_manager")
        self.ai_processor = None  # To be set externally if needed
    
    @st.cache_data(ttl=300)  # 5-minute cache (CACHE_TTL from config)
    def load_contacts_and_history(_self) -> Dict[str, Any]:
        """
        Load user contacts and conversation history
        
        Returns:
            Dictionary of contacts with their data and history
        """
        user_id = _self.auth_manager.get_current_user_id()
        if not user_id:
            _self.logger.warning("No user ID available for loading contacts")
            return {}
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            # Load contacts
            contacts_response = _self.supabase.table("contacts").select("*").eq("user_id", user_id).execute()
            contacts_data = {}
            
            for contact in contacts_response.data:
                contacts_data[contact["name"]] = {
                    "id": contact["id"],
                    "context": contact["context"],
                    "created_at": contact["created_at"],
                    "history": []
                }
            
            # Load messages
            messages_response = _self.supabase.table("messages").select("*").eq("user_id", user_id).order("created_at").execute()
            
            for msg in messages_response.data:
                contact_name = msg["contact_name"]
                if contact_name in contacts_data:
                    msg_time = utils.parse_timestamp(msg["created_at"])
                    contacts_data[contact_name]["history"].append({
                        "id": msg["id"],
                        "time": utils.format_timestamp(msg_time),
                        "type": msg["type"],
                        "original": msg["original"],
                        "result": msg["result"],
                        "healing_score": msg.get("healing_score", 0),
                        "model": msg.get("model", "Unknown"),
                        "sentiment": msg.get("sentiment", "unknown"),
                        "emotional_state": msg.get("emotional_state", "unknown")
                    })
            
            _self.logger.info(f"Loaded {len(contacts_data)} contacts with conversation history")
            return contacts_data
            
        except Exception as e:
            _self.logger.error(f"Failed to load contacts and history: {e}")
            st.warning(f"Could not load user data: {e}")
            return {}
    
    def save_contact(self, name: str, context: str, contact_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Save or update a contact
        
        Args:
            name: Contact name
            context: Relationship context
            contact_id: Existing contact ID for updates
            
        Returns:
            Contact data if successful, None otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not name.strip():
            from .ui.components import display_error
            display_error("Cannot save contact: User not logged in or invalid input.")
            return None
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            contact_data = {
                "name": utils.clean_contact_name(name),
                "context": context,
                "user_id": user_id,
                "updated_at": utils.get_current_timestamp()
            }
            
            if contact_id:
                # Update existing contact
                response = self.supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
            else:
                # Create new contact
                contact_data["created_at"] = utils.get_current_timestamp()
                response = self.supabase.table("contacts").insert(contact_data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved contact: {name}")
                self.clear_cache()
                return response.data[0]
            else:
                self.logger.error(f"Failed to save contact: {response}")
                from .ui.components import display_error
                display_error("Failed to save contact")
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
    
    def update_contact(self, contact_id: str, old_name: str, new_name: str, new_context: str) -> bool:
        """
        Update an existing contact
        
        Args:
            contact_id: Contact ID to update
            old_name: Current contact name
            new_name: New contact name
            new_context: New relationship context
            
        Returns:
            True if successful, False otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            from .ui.components import display_error
            display_error("Cannot update contact: User not logged in.")
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            contact_data = {
                "name": utils.clean_contact_name(new_name),
                "context": new_context,
                "updated_at": utils.get_current_timestamp()
            }
            
            # Update contact
            response = self.supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
            
            if response.data:
                # Update message records with new contact name if name changed
                if old_name != new_name:
                    self.supabase.table("messages").update({"contact_name": new_name}).eq("contact_id", contact_id).eq("user_id", user_id).execute()
                
                self.logger.info(f"Successfully updated contact: {old_name} -> {new_name}")
                self.clear_cache()
                return True
            else:
                self.logger.error(f"Failed to update contact: {response}")
                from .ui.components import display_error
                display_error("Failed to update contact")
                return False
                
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                from .ui.components import display_error
                display_error(f"A contact with the name '{new_name}' already exists.")
            else:
                self.logger.error(f"Error updating contact: {e}")
                from .ui.components import display_error
                display_error(f"Error updating contact: {e}")
            return False
    
    def delete_contact(self, contact_id: str, contact_name: str) -> bool:
        """
        Delete a contact and all associated messages
        
        Args:
            contact_id: ID of contact to delete
            contact_name: Name of contact to delete
            
        Returns:
            True if successful, False otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            from .ui.components import display_error
            display_error("Cannot delete contact: User not logged in or invalid input.")
            return False
        
        try:
            # Delete the contact (messages will be cascade deleted due to FK constraint)
            response = self.supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
            
            if response.data:
                # Clear any cached responses for this contact
                from .state_manager import state_manager
                state_manager.clear_last_response(contact_name)
                state_manager.clear_last_interpretation(contact_name)
                
                self.logger.info(f"Successfully deleted contact: {contact_name}")
                self.clear_cache()
                return True
            else:
                self.logger.error(f"Contact not found for deletion: {contact_id}")
                from .ui.components import display_error
                display_error("Contact not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting contact: {e}")
            from .ui.components import display_error
            display_error(f"Error deleting contact: {e}")
            return False
    
    def save_message(self, contact_id: str, contact_name: str, message_type: str, 
                    original: str, result: Optional[str], emotional_state: str, 
                    healing_score: int, model_used: str, sentiment: str = "unknown") -> bool:
        """
        Save a message to the database
        
        Args:
            contact_id: Contact ID
            contact_name: Contact name
            message_type: Type of message (incoming, translate, coach)
            original: Original message content
            result: AI response (optional)
            emotional_state: Detected emotional state
            healing_score: Healing score (1-10)
            model_used: AI model used
            sentiment: Message sentiment
            
        Returns:
            True if successful, False otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            from .ui.components import display_error
            display_error("Cannot save message: User not logged in.")
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            message_data = {
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
                "created_at": utils.get_current_timestamp()
            }
            
            response = self.supabase.table("messages").insert(message_data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved message for contact: {contact_name}")
                self.clear_cache()
                return True
            else:
                self.logger.error(f"Failed to save message: {response}")
                from .ui.components import display_error
                display_error("Failed to save message")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            from .ui.components import display_error
            display_error(f"Error saving message: {e}")
            return False
    
    def save_interpretation(self, contact_id: str, contact_name: str, original_message: str, 
                          interpretation: str, interpretation_score: int, model_used: str) -> bool:
        """
        Save interpretation to database
        
        Args:
            contact_id: Contact ID
            contact_name: Contact name
            original_message: Original message
            interpretation: AI interpretation
            interpretation_score: Interpretation quality score
            model_used: AI model used
            
        Returns:
            True if successful, False otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            interpretation_data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "original_message": original_message,
                "interpretation": interpretation,
                "interpretation_score": interpretation_score,
                "model": model_used,
                "user_id": user_id,
                "created_at": utils.get_current_timestamp()
            }
            
            response = self.supabase.table("interpretations").insert(interpretation_data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved interpretation for contact: {contact_name}")
                return True
            else:
                self.logger.error(f"Failed to save interpretation: {response}")
                return False
            
        except Exception as e:
            # For now, don't block if table doesn't exist yet
            self.logger.warning(f"Could not save interpretation: {e}")
            st.warning(f"Could not save interpretation: {e}")
            return False
    
    def save_feedback(self, rating: int, feedback_text: Optional[str], feature_context: str = "general") -> bool:
        """
        Save user feedback to database
        
        Args:
            rating: User rating (1-5)
            feedback_text: Optional feedback text
            feature_context: Context where feedback was given
            
        Returns:
            True if successful, False otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            feedback_data = {
                "user_id": user_id,
                "rating": rating,
                "feedback_text": feedback_text.strip() if feedback_text else None,
                "feature_context": feature_context,
                "created_at": utils.get_current_timestamp()
            }
            
            response = self.supabase.table("feedback").insert(feedback_data).execute()
            
            if response.data:
                self.logger.info(f"Successfully saved feedback: rating={rating}, context={feature_context}")
                return True
            else:
                self.logger.error(f"Failed to save feedback: {response}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error saving feedback: {e}")
            from .ui.components import display_error
            display_error(f"Error saving feedback: {e}")
            return False
    
    def get_cached_ai_response(self, contact_id: str, message_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached AI response if available
        
        Args:
            contact_id: Contact ID
            message_hash: Hash of the message
            
        Returns:
            Cached response data or None
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            return None
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            response = self.supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", utils.get_current_timestamp()).execute()
            
            if response.data:
                self.logger.debug(f"Found cached response for contact {contact_id}")
                return response.data[0]
            return None
            
        except Exception as e:
            # Cache errors shouldn't block the main flow
            self.logger.warning(f"Error getting cached response: {e}")
            return None
    
    def cache_ai_response(self, contact_id: str, message_hash: str, context: str, 
                         ai_response: str, healing_score: int, model: str, 
                         sentiment: str, emotional_state: str) -> bool:
        """
        Cache AI response for future use
        
        Args:
            contact_id: Contact ID
            message_hash: Hash of the message
            context: Relationship context
            ai_response: AI response text
            healing_score: Healing score
            model: AI model used
            sentiment: Message sentiment
            emotional_state: Emotional state
            
        Returns:
            True if successful, False otherwise
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            return False
        
        try:
            # Import here to avoid circular imports
            from .utils import utils
            
            # Set expiry to 24 hours from now
            expires_at = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59).isoformat()
            
            cache_data = {
                "contact_id": contact_id,
                "message_hash": message_hash,
                "context": context,
                "response": ai_response,
                "healing_score": healing_score,
                "model": model,
                "sentiment": sentiment,
                "emotional_state": emotional_state,
                "user_id": user_id,
                "expires_at": expires_at,
                "created_at": utils.get_current_timestamp()
            }
            
            response = self.supabase.table("ai_response_cache").insert(cache_data).execute()
            
            if response.data:
                self.logger.debug(f"Successfully cached AI response for contact {contact_id}")
                return True
            else:
                self.logger.warning(f"Failed to cache AI response: {response}")
                return False
            
        except Exception as e:
            # Cache errors shouldn't block the main flow
            self.logger.warning(f"Could not cache response: {e}")
            st.warning(f"Could not cache response: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear Streamlit cache for fresh data loading"""
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        self.logger.debug("Cleared data manager cache")
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics for dashboard
        
        Returns:
            Dictionary with user stats
        """
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            return {}
        
        try:
            # Get contact count
            contacts_response = self.supabase.table("contacts").select("id").eq("user_id", user_id).execute()
            contact_count = len(contacts_response.data)
            
            # Get message count
            messages_response = self.supabase.table("messages").select("id, healing_score").eq("user_id", user_id).execute()
            message_count = len(messages_response.data)
            
            # Calculate average healing score
            healing_scores = [msg.get("healing_score", 0) for msg in messages_response.data if msg.get("healing_score")]
            avg_healing_score = sum(healing_scores) / len(healing_scores) if healing_scores else 0
            
            stats = {
                "contact_count": contact_count,
                "message_count": message_count,
                "avg_healing_score": round(avg_healing_score, 1),
                "total_conversations": message_count
            }
            
            self.logger.info(f"Retrieved user stats: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Could not load user stats: {e}")
            st.warning(f"Could not load user stats: {e}")
            return {}

# No global instance - will be created in app.py