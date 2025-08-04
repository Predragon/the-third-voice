"""
Data Models for The Third Voice AI
Defines the core data structures used throughout the application
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Contact:
    """Contact data model"""
    id: str
    name: str
    context: str
    user_id: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Message:
    """Message data model"""
    id: str
    contact_id: str
    contact_name: str
    type: str
    original: str
    result: Optional[str]
    sentiment: Optional[str]
    emotional_state: Optional[str]
    model: Optional[str]
    healing_score: Optional[int]
    user_id: str
    created_at: datetime


@dataclass
class AIResponse:
    """AI response data model"""
    transformed_message: str
    healing_score: int
    sentiment: str
    emotional_state: str
    explanation: str
    subtext: str = ""
    needs: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.needs is None:
            self.needs = []
        if self.warnings is None:
            self.warnings = []
