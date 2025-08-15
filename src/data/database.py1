"""
Database Management Module for The Third Voice AI
Supabase database wrapper with error handling
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional
from supabase import create_client, Client

from .models import Contact, Message, AIResponse
from ..config.settings import AppConfig


class DatabaseManager:
    """Supabase database wrapper with error handling"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            AppConfig.get_supabase_url(),
            AppConfig.get_supabase_key()
        )
    
    def get_user_contacts(self, user_id: str) -> List[Contact]:
        """Get all contacts for a user"""
        try:
            response = self.supabase.table("contacts").select("*").eq("user_id", user_id).execute()
            contacts = []
            for contact_data in response.data:
                contacts.append(Contact(
                    id=contact_data["id"],
                    name=contact_data["name"],
                    context=contact_data["context"],
                    user_id=contact_data["user_id"],
                    created_at=datetime.fromisoformat(contact_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(contact_data["updated_at"].replace('Z', '+00:00'))
                ))
            return contacts
        except Exception as e:
            st.error(f"Error fetching contacts: {str(e)}")
            return []
    
    def create_contact(self, name: str, context: str, user_id: str) -> Optional[Contact]:
        """Create a new contact"""
        try:
            contact_data = {
                "name": name,
                "context": context,
                "user_id": user_id
            }
            response = self.supabase.table("contacts").insert(contact_data).execute()
            if response.data:
                data = response.data[0]
                return Contact(
                    id=data["id"],
                    name=data["name"],
                    context=data["context"],
                    user_id=data["user_id"],
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
                )
            return None
        except Exception as e:
            st.error(f"Error creating contact: {str(e)}")
            return None
    
    def save_message(self, contact_id: str, contact_name: str, message_type: str,
                    original: str, result: str, user_id: str, ai_response: AIResponse) -> bool:
        """Save a message to the database"""
        try:
            message_data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "type": message_type,
                "original": original,
                "result": result,
                "sentiment": ai_response.sentiment,
                "emotional_state": ai_response.emotional_state,
                "model": AppConfig.AI_MODEL,
                "healing_score": ai_response.healing_score,
                "user_id": user_id
            }
            response = self.supabase.table("messages").insert(message_data).execute()
            return len(response.data) > 0
        except Exception as e:
            st.error(f"Error saving message: {str(e)}")
            return False
    
    def get_conversation_history(self, contact_id: str, user_id: str) -> List[Message]:
        """Get conversation history for a contact"""
        try:
            response = (self.supabase.table("messages")
                       .select("*")
                       .eq("contact_id", contact_id)
                       .eq("user_id", user_id)
                       .order("created_at", desc=True)
                       .limit(50)
                       .execute())
            
            messages = []
            for msg_data in response.data:
                messages.append(Message(
                    id=msg_data["id"],
                    contact_id=msg_data["contact_id"],
                    contact_name=msg_data["contact_name"],
                    type=msg_data["type"],
                    original=msg_data["original"],
                    result=msg_data.get("result"),
                    sentiment=msg_data.get("sentiment"),
                    emotional_state=msg_data.get("emotional_state"),
                    model=msg_data.get("model"),
                    healing_score=msg_data.get("healing_score"),
                    user_id=msg_data["user_id"],
                    created_at=datetime.fromisoformat(msg_data["created_at"].replace('Z', '+00:00'))
                ))
            return messages
        except Exception as e:
            st.error(f"Error fetching conversation history: {str(e)}")
            return []
    
    def save_feedback(self, user_id: str, rating: int, feedback_text: str, feature_context: str) -> bool:
        """Save user feedback"""
        try:
            feedback_data = {
                "user_id": user_id,
                "rating": rating,
                "feedback_text": feedback_text,
                "feature_context": feature_context
            }
            response = self.supabase.table("feedback").insert(feedback_data).execute()
            return len(response.data) > 0
        except Exception as e:
            st.error(f"Error saving feedback: {str(e)}")
            return False
    
    def check_cache(self, contact_id: str, message_hash: str, user_id: str) -> Optional[AIResponse]:
        """Check if we have a cached response"""
        try:
            response = (self.supabase.table("ai_response_cache")
                       .select("*")
                       .eq("contact_id", contact_id)
                       .eq("message_hash", message_hash)
                       .eq("user_id", user_id)
                       .gt("expires_at", datetime.now().isoformat())
                       .execute())
            
            if response.data:
                data = response.data[0]
                return AIResponse(
                    transformed_message=data["response"],
                    healing_score=data["healing_score"],
                    sentiment=data["sentiment"],
                    emotional_state=data["emotional_state"],
                    explanation="From cache"
                )
            return None
        except:
            return None
    
    def save_to_cache(self, contact_id: str, message_hash: str, context: str,
                     response: str, user_id: str, ai_response: AIResponse) -> bool:
        """Save response to cache"""
        try:
            cache_data = {
                "contact_id": contact_id,
                "message_hash": message_hash,
                "context": context,
                "response": response,
                "healing_score": ai_response.healing_score,
                "model": AppConfig.AI_MODEL,
                "sentiment": ai_response.sentiment,
                "emotional_state": ai_response.emotional_state,
                "user_id": user_id,
                "expires_at": (datetime.now() + timedelta(days=AppConfig.CACHE_EXPIRY_DAYS)).isoformat()
            }
            response = self.supabase.table("ai_response_cache").insert(cache_data).execute()
            return len(response.data) > 0
        except:
            return False
    
    def clear_cache_entry(self, contact_id: str, message_hash: str, user_id: str) -> bool:
        """Clear a specific cache entry"""
        try:
            response = (self.supabase.table("ai_response_cache")
                       .delete()
                       .eq("contact_id", contact_id)
                       .eq("message_hash", message_hash)
                       .eq("user_id", user_id)
                       .execute())
            return True
        except Exception as e:
            print(f"Error clearing cache entry: {str(e)}")
            return False
