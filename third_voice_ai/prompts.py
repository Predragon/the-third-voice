# prompts.py - AI Prompt Templates for The Third Voice AI
# Centralized prompt management for consistent AI responses

from datetime import datetime
from typing import List, Dict, Any, Optional

class PromptManager:
    """Manages AI prompts with relationship context and conversation memory"""
    
    def __init__(self):
        self.base_system_prompt = """You are a compassionate relationship guide helping families heal through better communication. Your responses should be:
- Loving and understanding, never judgmental
- Practical and actionable
- Focused on healing and building connection
- Appropriate for the relationship context
- 2-3 paragraphs maximum for clarity"""
    
    def get_transformation_prompt(self, contact_name: str, context: str, message: str, 
                                history: Optional[List[Dict]] = None, is_incoming: bool = False) -> str:
        """Generate prompt for message transformation with relationship memory"""
        
        # Build relationship context
        relationship_context = self._build_relationship_context(history)
        
        # Determine message direction
        if is_incoming:
            mode_instruction = f"""
INCOMING MESSAGE from {contact_name}: They said something that may have triggered you or needs understanding.
Your task: Help the user understand what {contact_name} really means and suggest a loving response that heals rather than escalates."""
        else:
            mode_instruction = f"""
OUTGOING MESSAGE to {contact_name}: The user wants to say something that might come across poorly.
Your task: Reframe their message to be constructive, loving, and likely to strengthen the relationship."""
        
        context_description = self._get_context_description(context)
        
        prompt = f"""{self.base_system_prompt}

RELATIONSHIP CONTEXT: {context_description} with {contact_name}
{relationship_context}

{mode_instruction}

MESSAGE TO TRANSFORM: "{message}"

Provide guidance that:
1. Acknowledges the emotions involved
2. Offers a healing perspective or reframe
3. Suggests specific words or approach
4. Considers the {context} relationship dynamics
5. Aims for connection over being "right"

Keep your response concise, practical, and focused on healing this specific relationship."""

        return prompt
    
    def get_interpretation_prompt(self, contact_name: str, context: str, message: str, 
                                history: Optional[List[Dict]] = None) -> str:
        """Generate prompt for emotional subtext interpretation"""
        
        relationship_context = self._build_relationship_context(history, for_interpretation=True)
        context_description = self._get_context_description(context)
        
        prompt = f"""You are an expert relationship therapist analyzing emotional subtext with deep compassion.

RELATIONSHIP: {context_description} with {contact_name}
{relationship_context}

MESSAGE TO ANALYZE: "{message}"

Provide insights in exactly this format:

**🎭 EMOTIONAL SUBTEXT**
What they're really feeling beneath the words (1-2 sentences)

**💔 UNMET NEEDS** 
What they actually need but can't express (1-2 sentences)

**🌱 HEALING OPPORTUNITIES**
Specific ways to address their deeper needs (2-3 actionable suggestions)

**⚠️ WATCH FOR**
Relationship patterns or warning signs (1 sentence)

Be direct but loving. This person is trying to heal their family."""

        return prompt
    
    def get_feedback_analysis_prompt(self, feedback_text: str, rating: int, feature_context: str) -> str:
        """Generate prompt for analyzing user feedback"""
        
        prompt = f"""Analyze this user feedback for The Third Voice AI, a family healing communication app:

FEATURE CONTEXT: {feature_context}
RATING: {rating}/5 stars
FEEDBACK: "{feedback_text}"

Provide a brief analysis focusing on:
1. What's working well
2. Pain points or frustrations
3. Suggested improvements
4. User sentiment and satisfaction level

Keep response under 100 words, actionable for developers."""

        return prompt
    
    def get_conversation_summary_prompt(self, contact_name: str, context: str, 
                                     history: List[Dict]) -> str:
        """Generate prompt for summarizing conversation patterns"""
        
        if not history or len(history) < 3:
            return None
        
        # Prepare conversation data
        conversation_data = []
        for msg in history[-10:]:  # Last 10 messages
            if msg.get('original') and msg.get('healing_score'):
                conversation_data.append(f"Message: '{msg['original'][:50]}...' (Score: {msg['healing_score']}/10)")
        
        if not conversation_data:
            return None
        
        context_description = self._get_context_description(context)
        
        prompt = f"""Analyze conversation patterns for a {context_description} relationship with {contact_name}.

RECENT CONVERSATIONS:
{chr(10).join(conversation_data)}

Provide insights in this format:

**📈 PROGRESS TRENDS**
How communication is evolving (1-2 sentences)

**🎯 KEY THEMES** 
Main topics and patterns (1-2 sentences)

**💡 RECOMMENDATIONS**
Specific advice for continued healing (2-3 suggestions)

Focus on growth, patterns, and actionable next steps."""

        return prompt
    
    def _build_relationship_context(self, history: Optional[List[Dict]], 
                                  for_interpretation: bool = False) -> str:
        """Build relationship context from conversation history"""
        
        if not history or len(history) < 2:
            return "RELATIONSHIP STATUS: Early conversations - building understanding"
        
        # Analyze recent patterns
        recent_messages = history[-5:] if len(history) >= 5 else history
        patterns = []
        
        # Healing score trend
        scores = [msg.get('healing_score', 0) for msg in recent_messages if msg.get('healing_score')]
        if scores:
            avg_score = sum(scores) / len(scores)
            trend = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
            patterns.append(f"Healing trend: {trend} (avg: {avg_score:.1f}/10)")
        
        # Recent interaction samples (for interpretation mode)
        if for_interpretation and len(history) >= 3:
            recent_samples = []
            for msg in history[-3:]:
                if msg.get('original'):
                    recent_samples.append(f"Previous: '{msg['original'][:40]}...'")
            if recent_samples:
                patterns.extend(recent_samples)
        
        # Conversation frequency
        total_conversations = len(history)
        patterns.append(f"Total conversations: {total_conversations}")
        
        if patterns:
            return f"RELATIONSHIP CONTEXT:\n" + "\n".join(f"- {pattern}" for pattern in patterns)
        else:
            return "RELATIONSHIP CONTEXT: Limited history available"
    
    def _get_context_description(self, context: str) -> str:
        """Get human-readable description of relationship context"""
        
        context_descriptions = {
            "romantic": "romantic/intimate partnership",
            "coparenting": "co-parenting relationship",
            "workplace": "professional/workplace relationship", 
            "family": "family relationship",
            "friend": "friendship"
        }
        
        return context_descriptions.get(context, f"{context} relationship")
    
    def get_healing_score_explanation(self, score: int) -> str:
        """Get explanation for healing scores"""
        
        explanations = {
            10: "🌟 Perfect - Maximum healing potential, deeply transformative",
            9: "✨ Excellent - Very high healing potential, strong connection builder",
            8: "🌱 Great - High healing potential, clear relationship improvement",
            7: "💚 Good - Solid healing approach, positive relationship impact",
            6: "💛 Fair - Decent guidance with room for more healing focus",
            5: "🔧 Basic - Standard response, minimal healing enhancement",
            4: "⚠️ Below Average - Limited healing potential, needs improvement",
            3: "🔴 Poor - Low healing value, may not help much",
            2: "❌ Bad - Very limited benefit, likely ineffective",
            1: "💔 Terrible - No healing value, potentially harmful"
        }
        
        return explanations.get(score, f"Score: {score}/10")
    
    def get_context_specific_tips(self, context: str) -> List[str]:
        """Get relationship-specific communication tips"""
        
        tips = {
            "romantic": [
                "Use 'I feel' statements instead of 'You always/never'",
                "Address the need behind the emotion",
                "Focus on solving together, not winning",
                "Physical affection can help during difficult conversations"
            ],
            "coparenting": [
                "Keep focus on the children's wellbeing",
                "Separate your hurt from parenting decisions", 
                "Use business-like tone when emotions are high",
                "Remember: you're teammates for your kids' sake"
            ],
            "workplace": [
                "Maintain professional boundaries while being human",
                "Focus on work impact rather than personal feelings",
                "Seek win-win solutions that benefit the team",
                "Document important conversations professionally"
            ],
            "family": [
                "Honor family history while setting healthy boundaries",
                "Respect generational differences in communication styles",
                "Focus on love beneath family dysfunction patterns",
                "Remember: you can't change them, only your response"
            ],
            "friend": [
                "Friendships require mutual effort and understanding",
                "Address conflicts directly but gently",
                "Allow space for different life phases and priorities",
                "True friends want the best for each other"
            ]
        }
        
        return tips.get(context, [
            "Listen to understand, not to respond",
            "Speak from love, even when you're hurt",
            "Focus on healing the relationship, not being right",
            "Take breaks when emotions get too intense"
        ])
    
    def get_emergency_prompts(self) -> Dict[str, str]:
        """Get prompts for crisis/emergency situations"""
        
        return {
            "crisis_detection": """Analyze this message for signs of crisis (suicide ideation, domestic violence, severe mental health crisis, threats of harm):

MESSAGE: "{message}"

If you detect ANY crisis indicators, respond with:
CRISIS: YES - [brief explanation]
RESOURCES: [appropriate crisis resources]

If no crisis detected:
CRISIS: NO

Be extremely cautious - err on the side of safety.""",
            
            "safety_first": """This message may indicate a safety concern. Your response should:
1. Prioritize safety over relationship healing
2. Suggest professional help resources
3. Avoid giving advice that could escalate danger
4. Be supportive but clear about limitations

Remember: Some situations require professional intervention, not AI guidance."""
        }

# Create global instance
prompt_manager = PromptManager()

# Convenience functions for easy import
def get_transformation_prompt(*args, **kwargs):
    return prompt_manager.get_transformation_prompt(*args, **kwargs)

def get_interpretation_prompt(*args, **kwargs):
    return prompt_manager.get_interpretation_prompt(*args, **kwargs)

def get_healing_score_explanation(score: int):
    return prompt_manager.get_healing_score_explanation(score)

def get_context_tips(context: str):
    return prompt_manager.get_context_specific_tips(context)
