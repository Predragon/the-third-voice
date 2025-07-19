"""
AI prompts and context templates for The Third Voice
Each prompt is crafted with emotional intelligence and purpose
"""

# Context-specific prompts for different relationships
COACHING_PROMPTS = {
    "general": (
        "You are an emotionally intelligent communication coach. "
        "Help improve this message for clarity and empathy. "
        "Focus on being clear, kind, and constructive."
    ),
    
    "romantic": (
        "You help reframe romantic messages with empathy and clarity "
        "while maintaining intimacy. Preserve the love and connection "
        "while ensuring the message is received with care."
    ),
    
    "coparenting": (
        "You offer emotionally safe responses for coparenting focused "
        "on the children's wellbeing. Keep communication child-centered, "
        "respectful, and solution-oriented. Remember: the kids come first."
    ),
    
    "workplace": (
        "You translate workplace messages for professional tone and "
        "clear intent. Maintain professionalism while ensuring the "
        "message is direct, respectful, and actionable."
    ),
    
    "family": (
        "You understand family dynamics and help rephrase for better "
        "family relationships. Consider family history, respect boundaries, "
        "and promote healing and understanding."
    ),
    
    "friend": (
        "You assist with friendship communication to strengthen bonds "
        "and resolve conflicts. Focus on maintaining the friendship "
        "while addressing issues honestly and supportively."
    )
}

def get_system_prompt(context: str, is_received: bool = False) -> str:
    """
    Generate system prompt based on context and message type
    
    Args:
        context: The relationship context (general, romantic, etc.)
        is_received: True if analyzing a received message, False if coaching outbound
        
    Returns:
        Formatted system prompt for the AI
    """
    base_prompt = COACHING_PROMPTS.get(context, COACHING_PROMPTS["general"])
    
    if is_received:
        action_prompt = (
            "Analyze this received message and suggest how to respond. "
            "Help understand the underlying emotions and needs, then "
            "provide guidance on how to reply with empathy and wisdom."
        )
    else:
        action_prompt = (
            "Improve this message before sending. Make it clearer, "
            "more empathetic, and more likely to achieve positive outcomes. "
            "Maintain the sender's authentic voice while enhancing the message."
        )
    
    return f"{base_prompt} {action_prompt}"

def create_message_payload(message: str, context: str, is_received: bool = False) -> list:
    """
    Create the message payload for AI API
    
    Args:
        message: The user's message
        context: Relationship context
        is_received: Whether this is a received message to analyze
        
    Returns:
        Formatted messages array for API call
    """
    system_prompt = get_system_prompt(context, is_received)
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Message: {message}"}
    ]

# Special prompts for different scenarios
EMERGENCY_PROMPTS = {
    "conflict": (
        "This seems like a tense situation. Focus on de-escalation, "
        "finding common ground, and preventing further harm to the relationship."
    ),
    
    "apology": (
        "This appears to be an apology. Help make it sincere, specific, "
        "and focused on repair rather than justification."
    ),
    
    "difficult_news": (
        "This seems to contain difficult news. Help deliver it with "
        "compassion, clarity, and support for the recipient."
    )
}

def detect_message_type(message: str) -> str:
    """
    Simple detection of message type for special handling
    
    Args:
        message: The message to analyze
        
    Returns:
        Message type identifier
    """
    message_lower = message.lower()
    
    # Check for conflict indicators
    if any(word in message_lower for word in ['angry', 'upset', 'frustrated', 'mad', 'hate']):
        return "conflict"
    
    # Check for apology indicators  
    if any(word in message_lower for word in ['sorry', 'apologize', 'my fault', 'forgive']):
        return "apology"
    
    # Check for difficult news indicators
    if any(word in message_lower for word in ['bad news', 'problem', 'issue', 'concern', 'worried']):
        return "difficult_news"
    
    return "normal"
