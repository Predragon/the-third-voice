from supabase import create_client, Client
from third_voice_ai.config import Config
from third_voice_ai.auth_manager import AuthManager
from third_voice_ai.utils import get_current_timestamp
from third_voice_ai.ui.components import display_error
from loguru import logger
from typing import Optional, Dict, Any
import streamlit as st

class DataManager:
    def __init__(self, config: Config, auth_manager: AuthManager):
        self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
        self.config = config
        self.auth_manager = auth_manager
        self.ai_processor = None  # To be set externally if needed

    @st.cache_data(ttl=300)  # 5-minute cache
    def load_contacts_and_history(self) -> Dict[str, Any]:
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            return {}
        try:
            contacts_response = self.supabase.table("contacts").select("*").eq("user_id", user_id).execute()
            contacts_data = {contact["name"]: {
                "id": contact["id"], "context": contact["context"], "created_at": contact["created_at"], "history": []
            } for contact in contacts_response.data}
            messages_response = self.supabase.table("messages").select("*").eq("user_id", user_id).order("created_at").execute()
            for msg in messages_response.data:
                if msg["contact_name"] in contacts_data:
                    contacts_data[msg["contact_name"]]["history"].append({
                        "id": msg["id"], "time": get_current_timestamp(), "type": msg["type"], "original": msg["original"],
                        "result": msg["result"], "healing_score": msg.get("healing_score", 0), "model": msg.get("model", "Unknown"),
                        "sentiment": msg.get("sentiment", "unknown"), "emotional_state": msg.get("emotional_state", "unknown")
                    })
            return contacts_data
        except Exception as e:
            logger.error(f"Failed to load contacts and history: {e}")
            display_error("Could not load data. Please try again.")
            return {}

    def save_contact(self, name: str, context: str, contact_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not name.strip():
            display_error("Cannot save contact: User not logged in or invalid input.")
            return None
        try:
            contact_data = {
                "name": utils.clean_contact_name(name), "context": context, "user_id": user_id,
                "updated_at": get_current_timestamp()
            }
            if contact_id:
                response = self.supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
            else:
                contact_data["created_at"] = get_current_timestamp()
                response = self.supabase.table("contacts").insert(contact_data).execute()
            if response.data:
                logger.debug(f"Inserted/updated contact: {response.data[0]}")
                st.cache_data.clear()
                return response.data[0]  # Return the created/updated contact data
            logger.error(f"Failed to save contact: {response.error}")
            display_error("Failed to save contact.")
            return None
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                display_error(f"A contact with the name '{name}' already exists.")
            else:
                logger.error(f"Error saving contact: {e}")
                display_error(f"Error saving contact: {e}")
            return None

    def save_message(self, contact_id: str, contact_name: str, message_type: str, original: str, result: str, 
                     emotional_state: str, healing_score: int, model_used: str, sentiment: str) -> bool:
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            display_error("Cannot save message: User not logged in or invalid contact.")
            return False
        try:
            data = {
                "contact_id": contact_id, "contact_name": contact_name, "type": message_type, "original": original,
                "result": result, "emotional_state": emotional_state, "healing_score": healing_score, "model": model_used,
                "sentiment": sentiment, "user_id": user_id, "created_at": get_current_timestamp()
            }
            response = self.supabase.table("messages").insert(data).execute()
            if response.data:
                logger.debug(f"Save message response: {response.data}")
                st.cache_data.clear()
                return True
            logger.error(f"Failed to save message: {response.error}")
            display_error("Failed to save message.")
            return False
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            display_error(f"Error saving message: {e}")
            return False

    def save_interpretation(self, contact_id: str, contact_name: str, original_message: str, interpretation: str, 
                           interpretation_score: int, model_used: str) -> bool:
        user_id = self.auth_manager.get_current_user_id()
        if not user_id or not contact_id:
            display_error("Cannot save interpretation: User not logged in or invalid contact.")
            return False
        try:
            data = {
                "contact_id": contact_id, "contact_name": contact_name, "type": "interpretation", "original": original_message,
                "result": interpretation, "healing_score": interpretation_score, "model": model_used, "sentiment": "neutral",
                "emotional_state": "calm", "user_id": user_id, "created_at": get_current_timestamp()
            }
            response = self.supabase.table("messages").insert(data).execute()
            if response.data:
                logger.debug(f"Save interpretation response: {response.data}")
                st.cache_data.clear()
                return True
            logger.error(f"Failed to save interpretation: {response.error}")
            display_error("Failed to save interpretation.")
            return False
        except Exception as e:
            logger.error(f"Error saving interpretation: {e}")
            display_error(f"Could not save interpretation: {e}")
            return False