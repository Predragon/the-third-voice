# data_manager.py - The Third Voice AI Data Management
# Supabase database operations with mobile-friendly caching

import streamlit as st
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from auth_manager import auth_manager
from utils import utils
from config import CACHE_TTL

class DataManager:
    """
    Database manager for The Third Voice AI
    Handles all Supabase operations with intelligent caching
    """
    
    def __init__(self):
        """Initialize with Supabase client from auth manager"""
        self.supabase = auth_manager.supabase
    
    @st.cache_data(ttl=CACHE_TTL)
    def load_contacts_and_history(_self) -> Dict[str, Any]:
        """
        Load user contacts and conversation history
        
        Returns:
            Dictionary of contacts with their data and history
        """
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            return {}
        
        try:
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
            
            return contacts_data
            
        except Exception as e:
            st.warning(f"Could not load user data: {e}")
            return {}
    
    def save_contact(self, name: str, context: str, contact_id: Optional[str] = None) -> bool:
        """
        Save or update a contact
        
        Args:
            name: Contact name
            context: Relationship context
            contact_id: Existing contact ID for updates
            
        Returns:
            True if successful, False otherwise
        """
        user_id = auth_manager.get_current_user_id()
        if not user_id or not name.strip():
            st.error("Cannot save contact: User not logged in or invalid input.")
            return False
        
        try:
            contact_data = {
                "name": utils.clean_contact_name(name),
                "context": context,
                "user_id": user_id,
                "updated_at": utils.get_current_utc_timestamp()
            }
            
            if contact_id:
                # Update existing contact
                response = self.supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
            else:
                # Create new contact
                contact_data["created_at"] = utils.get_current_utc_timestamp()
                response = self.supabase.table("contacts").insert(contact_data).execute()
            
            if response.data:
                self.clear_cache()
                return True
            else:
                st.error("Failed to save contact")
                return False
                
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                st.error(f"A contact with the name '{name}' already exists.")
            else:
                st.error(f"Error saving contact: {e}")
            return False
    
    def delete_contact(self, contact_id: str) -> bool:
        """
        Delete a contact and all associated messages
        
        Args:
            contact_id: ID of contact to delete
            
        Returns:
            True if successful, False otherwise
        """
        user_id = auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            st.error("Cannot delete contact: User not logged in or invalid input.")
            return False
        
        try:
            # Get contact info first
            contact_response = self.supabase.table("contacts").select("name").eq("id", contact_id).eq("user_id", user_id).execute()
            
            if contact_response.data:
                contact_name = contact_response.data[0]["name"]
                
                # Delete the contact (messages will be cascade deleted due to FK constraint)
                self.supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
                
                # Clear any cached responses for this contact
                from state_manager import state_manager
                state_manager.clear_last_response(contact_name)
                state_manager.clear_last_interpretation(contact_name)
                
                self.clear_cache()
                return True
            else:
                st.error("Contact not found")
                return False
                
        except Exception as e:
            st.error(f"Error deleting contact: {e}")
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
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            st.error("Cannot save message: User not logged in.")
            return False
        
        try:
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
                "created_at": utils.get_current_utc_timestamp()
            }
            
            response = self.supabase.table("messages").insert(message_data).execute()
            
            if response.data:
                self.clear_cache()
                return True
            else:
                st.error("Failed to save message")
                return False
                
        except Exception as e:
            st.error(f"Error saving message: {e}")
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
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            return False
        
        try:
            interpretation_data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "original_message": original_message,
                "interpretation": interpretation,
                "interpretation_score": interpretation_score,
                "model": model_used,
                "user_id": user_id,
                "created_at": utils.get_current_utc_timestamp()
            }
            
            response = self.supabase.table("interpretations").insert(interpretation_data).execute()
            return bool(response.data)
            
        except Exception as e:
            # For now, don't block if table doesn't exist yet
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
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            return False
        
        try:
            feedback_data = {
                "user_id": user_id,
                "rating": rating,
                "feedback_text": feedback_text.strip() if feedback_text else None,
                "feature_context": feature_context,
                "created_at": utils.get_current_utc_timestamp()
            }
            
            response = self.supabase.table("feedback").insert(feedback_data).execute()
            return bool(response.data)
            
        except Exception as e:
            st.error(f"Error saving feedback: {e}")
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
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            return None
        
        try:
            response = self.supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", utils.get_current_utc_timestamp()).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            # Cache errors shouldn't block the main flow
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
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            return False
        
        try:
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
                "created_at": utils.get_current_utc_timestamp()
            }
            
            response = self.supabase.table("ai_response_cache").insert(cache_data).execute()
            return bool(response.data)
            
        except Exception as e:
            # Cache errors shouldn't block the main flow
            st.warning(f"Could not cache response: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear Streamlit cache for fresh data loading"""
        st.cache_data.clear()
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics for dashboard
        
        Returns:
            Dictionary with user stats
        """
        user_id = auth_manager.get_current_user_id()
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
            
            return {
                "contact_count": contact_count,
                "message_count": message_count,
                "avg_healing_score": round(avg_healing_score, 1),
                "total_conversations": message_count
            }
            
        except Exception as e:
            st.warning(f"Could not load user stats: {e}")
            return {}

# Global data manager instance
data_manager = DataManager()
