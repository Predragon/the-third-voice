# prompts.py - Prompt management for The Third Voice AI

from typing import List, Dict, Optional
import streamlit as st

class PromptManager:
    """Manages AI prompts for message transformation, interpretation, and relationship analysis"""
    
    @staticmethod
    def get_transformation_prompt(
        contact_name: str,
        context: str,
        message: str,
        history: Optional[List[Dict]] = None,
        is_incoming: bool = False
    ) -> str:
        """
        Generate system prompt for message transformation
        
        Args:
            contact_name: Name of the contact
            context: Relationship context (e.g., family, romantic)
            message: Input message
            history: Conversation history
            is_incoming: Whether the message is incoming (True) or outgoing (False)
            
        Returns:
            System prompt string
        """
        logger = st.get_logger(__name__)
        context_keywords = {
            "family": "trust, support, family roles, emotional safety, togetherness",
            "romantic": "intimacy, partnership, vulnerability, affection",
            "coparenting": "cooperation, parenting, respect, shared responsibility",
            "workplace": "professionalism, collaboration, clarity, teamwork",
            "friend": "loyalty, fun, mutual support, camaraderie"
        }
        
        base_prompt = f"""
        You are The Third Voice AI, a compassionate assistant helping users communicate with love and understanding in their relationships. Your role is to transform messages to promote healing, empathy, and connection, especially in emotionally charged situations. You are assisting with a {context} relationship for a contact named {contact_name}. Use a warm, supportive tone and emphasize {context_keywords.get(context, 'empathy, connection')} to tailor the response.

        Instructions:
        - For incoming messages (from {contact_name} to the user):
          - Rephrase the message to soften its tone, clarify intent, and suggest a loving, constructive response the user can give.
          - Acknowledge the emotions behind {contact_name}'s words and offer a perspective that fosters understanding.
        - For outgoing messages (from the user to {contact_name}):
          - Coach the user to express their feelings in a way that is kind, clear, and promotes healing.
          - Avoid blame or defensiveness; use 'I' statements and empathy.
        - Consider the {context} relationship dynamics (e.g., {context_keywords.get(context, 'empathy, connection')} for a {context} context).
        - If history is provided, incorporate emotional patterns or recurring themes to make the response more relevant.
        - Keep responses concise (100-200 words), empathetic, and actionable.
        - Avoid generic responses; tailor the tone and content to the specific message and context.
        - If the message is ambiguous, infer likely emotions based on the {context} context.

        Current message: {message}
        """

        if history and len(history) > 0:
            recent_history = history[-3:]  # Last 3 messages for context
            history_summary = "\nRecent conversation history:\n"
            for msg in recent_history:
                history_summary += f"- {msg['time']}: {msg['original'][:200]}... (Type: {msg['type']}, Healing Score: {msg.get('healing_score', 'N/A')}, Sentiment: {msg.get('sentiment', 'N/A')})\n"
            base_prompt += history_summary
            base_prompt += "\nUse this history to identify emotional patterns (e.g., frustration, support) and tailor your response accordingly."
        else:
            base_prompt += "\nNo conversation history is available. Focus on the current message and {context} context to provide a relevant response."

        if is_incoming:
            base_prompt += f"""
            This is an incoming message from {contact_name}. Rephrase their message to highlight the underlying emotions and suggest a response that fosters connection and understanding in the {context} context.
            """
        else:
            base_prompt += f"""
            This is an outgoing message from the user to {contact_name}. Coach the user to rephrase their message in a way that promotes healing and empathy in the {context} context.
            """

        logger.debug(f"Generated transformation prompt for {contact_name}, context: {context}, length: {len(base_prompt)}")
        return base_prompt

    @staticmethod
    def get_interpretation_prompt(
        contact_name: str,
        context: str,
        message: str,
        history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate system prompt for message interpretation
        
        Args:
            contact_name: Name of the contact
            context: Relationship context
            message: Message to interpret
            history: Conversation history
            
        Returns:
            System prompt string
        """
        logger = st.get_logger(__name__)
        context_keywords = {
            "family": "trust, support, family roles, emotional safety, togetherness",
            "romantic": "intimacy, partnership, vulnerability, affection",
            "coparenting": "cooperation, parenting, respect, shared responsibility",
            "workplace": "professionalism, collaboration, clarity, teamwork",
            "friend": "loyalty, fun, mutual support, camaraderie"
        }
        
        prompt = f"""
        You are The Third Voice AI, a compassionate assistant analyzing emotional subtext in messages to help users understand their relationships. Your role is to interpret the message below from {contact_name} in a {context} relationship, identifying underlying emotions, unmet needs, and opportunities for healing. Use a warm, empathetic tone to make the user feel supported, and emphasize {context_keywords.get(context, 'empathy, connection')} to tailor the response.

        Instructions:
        - Analyze the emotional subtext of the message (e.g., frustration, longing, appreciation).
        - Identify unmet needs or desires {contact_name} may be expressing (e.g., respect, acknowledgment).
        - Suggest specific, actionable ways the user can respond to foster healing and connection.
        - Highlight potential pitfalls to avoid (e.g., defensive responses, dismissing feelings).
        - Structure the response with clear sections:
          - **🎭 EMOTIONAL SUBTEXT**: What emotions or intentions are beneath the words?
          - **💔 UNMET NEEDS**: What does {contact_name} need based on this message?
          - **🌱 HEALING OPPORTUNITIES**: How can the user respond to promote understanding?
          - **⚠️ WATCH FOR**: What to avoid to prevent escalation?
        - Keep the response concise (150-250 words) and tailored to the {context} context.
        - If history is provided, use it to identify recurring emotional patterns.

        Message to analyze: {message}
        """

        if history and len(history) > 0:
            recent_history = history[-3:]  # Last 3 messages for context
            history_summary = "\nRecent conversation history:\n"
            for msg in recent_history:
                history_summary += f"- {msg['time']}: {msg['original'][:200]}... (Type: {msg['type']}, Healing Score: {msg.get('healing_score', 'N/A')}, Sentiment: {msg.get('sentiment', 'N/A')})\n"
            prompt += history_summary
            prompt += "\nUse this history to contextualize the emotional subtext and tailor your analysis."
        else:
            prompt += "\nNo conversation history is available. Focus on the current message and {context} context to provide a relevant analysis."

        logger.debug(f"Generated interpretation prompt for {contact_name}, context: {context}, length: {len(prompt)}")
        return prompt

    @staticmethod
    def get_healing_score_explanation(score: int) -> str:
        """
        Provide explanation for healing score
        
        Args:
            score: Healing score (0-10)
            
        Returns:
            Explanation string
        """
        logger = st.get_logger(__name__)
        explanations = {
            range(8, 11): f"{score}/10: High healing potential! This response fosters deep connection and understanding in the relationship.",
            range(6, 8): f"{score}/10: Good healing potential. This response promotes empathy and constructive dialogue.",
            range(4, 6): f"{score}/10: Moderate healing potential. This response is a step toward understanding but could be more empathetic.",
            range(0, 4): f"{score}/10: Limited healing potential. Consider softening the tone or addressing emotions more directly."
        }
        
        for score_range, explanation in explanations.items():
            if score in score_range:
                logger.debug(f"Healing score explanation: {explanation}")
                return explanation
        return f"{score}/10: Invalid score. Please ensure score is between 0 and 10."

    @staticmethod
    def get_relationship_health_prompt(
        contact_name: str,
        context: str,
        history: List[Dict]
    ) -> str:
        """
        Generate system prompt for relationship health analysis
        
        Args:
            contact_name: Name of the contact
            context: Relationship context
            history: Conversation history
            
        Returns:
            System prompt string
        """
        logger = st.get_logger(__name__)
        context_keywords = {
            "family": "trust, support, family roles, emotional safety, togetherness",
            "romantic": "intimacy, partnership, vulnerability, affection",
            "coparenting": "cooperation, parenting, respect, shared responsibility",
            "workplace": "professionalism, collaboration, clarity, teamwork",
            "friend": "loyalty, fun, mutual support, camaraderie"
        }
        
        prompt = f"""
        You are The Third Voice AI, a compassionate assistant analyzing conversation history to assess the health of a {context} relationship with {contact_name}. Your role is to provide a concise summary of the relationship's emotional health, focusing on {context_keywords.get(context, 'empathy, connection')}. 

        Instructions:
        - Analyze the provided conversation history to identify patterns (e.g., recurring emotions, communication styles).
        - Provide a brief assessment (100-150 words) of the relationship's health, including:
          - **Strengths**: Positive patterns (e.g., empathy, support).
          - **Challenges**: Areas of tension or unmet needs.
          - **Recommendations**: Actionable steps to improve the relationship.
        - Use a warm, encouraging tone to inspire the user to continue their healing journey.
        - Tailor the analysis to the {context} context.

        Conversation history:
        """
        
        if history and len(history) > 0:
            recent_history = history[-5:]  # Last 5 messages for context
            history_summary = "\n"
            for msg in recent_history:
                history_summary += f"- {msg['time']}: {msg['original'][:200]}... (Type: {msg['type']}, Healing Score: {msg.get('healing_score', 'N/A')}, Sentiment: {msg.get('sentiment', 'N/A')})\n"
            prompt += history_summary
        else:
            prompt += "\nNo conversation history is available. Provide a general assessment based on the {context} context."

        prompt += "\nBased on this, provide a relationship health assessment."
        logger.debug(f"Generated relationship health prompt for {contact_name}, context: {context}, length: {len(prompt)}")
        return prompt

    @staticmethod
    def get_feedback_analysis_prompt(
        feedback_text: str,
        feature_context: str,
        rating: int
    ) -> str:
        """
        Generate system prompt for analyzing user feedback
        
        Args:
            feedback_text: User-provided feedback
            feature_context: Feature or context of the feedback
            rating: Feedback rating (1-5)
            
        Returns:
            System prompt string
        """
        logger = st.get_logger(__name__)
        prompt = f"""
        You are The Third Voice AI, analyzing user feedback to improve the application. Your role is to interpret the feedback provided below, focusing on the {feature_context} feature, and provide insights to enhance the user experience.

        Instructions:
        - Analyze the feedback text and rating ({rating}/5) to identify:
          - **User Sentiment**: Positive, neutral, or negative emotions.
          - **Key Themes**: Specific praises, criticisms, or suggestions.
          - **Actionable Improvements**: Practical steps to address the feedback.
        - Structure the response with:
          - **📊 SENTIMENT**: What is the user's overall sentiment?
          - **🔍 KEY THEMES**: What are the main points or concerns?
          - **🛠️ IMPROVEMENTS**: How can the {feature_context} feature be improved?
        - Keep the response concise (100-150 words) and actionable.
        - Use a neutral, professional tone.

        Feedback text: {feedback_text}
        Rating: {rating}/5
        """
        logger.debug(f"Generated feedback analysis prompt for feature: {feature_context}, rating: {rating}")
        return prompt
