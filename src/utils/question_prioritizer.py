"""
Question Prioritizer
Assigns priority levels to questions based on feature type and question content.
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class PriorityLevel(Enum):
    """Priority levels for questions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class QuestionPriority:
    """Question with priority information."""
    question: str
    priority: PriorityLevel
    score: float
    reasoning: str


class QuestionPrioritizer:
    """
    Prioritizes questions based on feature type and question content.
    
    Priority factors:
    - Feature type (some types have inherently higher priority questions)
    - Question keywords (security, authentication, data integrity are high priority)
    - Question complexity (simple questions are lower priority)
    - Business impact (questions affecting core functionality are higher priority)
    """
    
    def __init__(self):
        """Initialize the prioritizer with priority patterns."""
        self.priority_patterns = self._initialize_priority_patterns()
        self.feature_type_weights = self._initialize_feature_type_weights()
    
    def _initialize_priority_patterns(self) -> Dict[PriorityLevel, Dict]:
        """Initialize priority patterns and keywords."""
        return {
            PriorityLevel.CRITICAL: {
                "keywords": [
                    "security", "authentication", "authorization", "password", "login",
                    "data protection", "privacy", "compliance", "gdpr", "hipaa",
                    "payment", "billing", "financial", "money", "credit card",
                    "user data", "personal information", "confidential"
                ],
                "patterns": [
                    r"security.*(requirement|measure|protection)",
                    r"authentication.*(method|system|process)",
                    r"payment.*(process|gateway|method)",
                    r"data.*(protection|privacy|confidential)",
                    r"compliance.*(requirement|regulation)"
                ],
                "weight": 1.0
            },
            PriorityLevel.HIGH: {
                "keywords": [
                    "user", "account", "registration", "profile", "settings",
                    "core functionality", "main feature", "primary", "essential",
                    "performance", "scalability", "reliability", "availability",
                    "integration", "api", "external", "third party"
                ],
                "patterns": [
                    r"user.*(account|registration|profile)",
                    r"core.*(functionality|feature)",
                    r"main.*(feature|functionality)",
                    r"performance.*(requirement|expectation)",
                    r"integration.*(api|external)"
                ],
                "weight": 0.8
            },
            PriorityLevel.MEDIUM: {
                "keywords": [
                    "interface", "design", "layout", "ui", "ux", "user experience",
                    "notification", "email", "sms", "alert", "reminder",
                    "search", "filter", "sort", "organize", "categorize",
                    "report", "analytics", "dashboard", "metrics"
                ],
                "patterns": [
                    r"interface.*(design|layout)",
                    r"notification.*(email|sms|alert)",
                    r"search.*(functionality|feature)",
                    r"report.*(generate|view|analytics)"
                ],
                "weight": 0.6
            },
            PriorityLevel.LOW: {
                "keywords": [
                    "nice to have", "optional", "additional", "extra", "bonus",
                    "cosmetic", "aesthetic", "visual", "animation", "theme",
                    "preference", "customization", "personalization"
                ],
                "patterns": [
                    r"nice.*to.*have",
                    r"optional.*(feature|functionality)",
                    r"cosmetic.*(change|improvement)",
                    r"visual.*(enhancement|improvement)"
                ],
                "weight": 0.4
            }
        }
    
    def _initialize_feature_type_weights(self) -> Dict[str, float]:
        """Initialize feature type weights for priority calculation."""
        return {
            "authentication": 1.0,  # Security-critical
            "payment": 1.0,         # Financial-critical
            "crud": 0.8,            # Core functionality
            "integration": 0.8,     # External dependencies
            "workflow": 0.8,        # Business processes
            "reporting": 0.6,       # Analytics and insights
            "notification": 0.6,    # Communication
            "search": 0.6,          # Discovery
            "ui": 0.5,              # User interface
            "general": 0.5          # General features
        }
    
    def prioritize_questions(self, questions: List[str], feature_type: str = "general") -> List[QuestionPriority]:
        """
        Prioritize a list of questions based on feature type and content.
        
        Args:
            questions (List[str]): List of questions to prioritize
            feature_type (str): The feature type for context
            
        Returns:
            List[QuestionPriority]: List of questions with priority information
        """
        prioritized_questions = []
        
        for question in questions:
            priority_info = self._calculate_question_priority(question, feature_type)
            prioritized_questions.append(priority_info)
        
        # Sort by priority (critical -> high -> medium -> low)
        priority_order = [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW]
        prioritized_questions.sort(key=lambda x: priority_order.index(x.priority))
        
        return prioritized_questions
    
    def _calculate_question_priority(self, question: str, feature_type: str) -> QuestionPriority:
        """
        Calculate priority for a single question.
        
        Args:
            question (str): The question to analyze
            feature_type (str): The feature type for context
            
        Returns:
            QuestionPriority: Priority information for the question
        """
        question_lower = question.lower()
        max_score = 0.0
        best_priority = PriorityLevel.MEDIUM
        reasoning_parts = []
        
        # Calculate scores for each priority level
        for priority_level, config in self.priority_patterns.items():
            score = 0.0
            
            # Check keyword matches
            keyword_matches = []
            for keyword in config["keywords"]:
                if keyword in question_lower:
                    score += 1.0
                    keyword_matches.append(keyword)
            
            # Check pattern matches (weighted higher)
            pattern_matches = []
            for pattern in config["patterns"]:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    score += 2.0
                    pattern_matches.append(pattern)
            
            # Apply priority weight
            score *= config["weight"]
            
            # Apply feature type weight
            feature_weight = self.feature_type_weights.get(feature_type, 0.5)
            score *= feature_weight
            
            if score > max_score:
                max_score = score
                best_priority = priority_level
                
                # Build reasoning
                if keyword_matches:
                    reasoning_parts.append(f"Keywords: {', '.join(keyword_matches)}")
                if pattern_matches:
                    reasoning_parts.append(f"Patterns: {', '.join(pattern_matches)}")
                reasoning_parts.append(f"Feature type: {feature_type} (weight: {feature_weight})")
        
        # Determine final priority based on score
        final_priority = self._score_to_priority(max_score, feature_type)
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else f"Default priority for {feature_type} feature"
        
        return QuestionPriority(
            question=question,
            priority=final_priority,
            score=max_score,
            reasoning=reasoning
        )
    
    def _score_to_priority(self, score: float, feature_type: str) -> PriorityLevel:
        """
        Convert a score to a priority level.
        
        Args:
            score (float): The calculated priority score
            feature_type (str): The feature type for context
            
        Returns:
            PriorityLevel: The determined priority level
        """
        # Adjust thresholds based on feature type
        if feature_type in ["authentication", "payment"]:
            # Higher thresholds for security/financial features
            if score >= 3.0:
                return PriorityLevel.CRITICAL
            elif score >= 2.0:
                return PriorityLevel.HIGH
            elif score >= 1.0:
                return PriorityLevel.MEDIUM
            else:
                return PriorityLevel.LOW
        else:
            # Standard thresholds for other features
            if score >= 2.5:
                return PriorityLevel.CRITICAL
            elif score >= 1.5:
                return PriorityLevel.HIGH
            elif score >= 0.8:
                return PriorityLevel.MEDIUM
            else:
                return PriorityLevel.LOW
    
    def get_priority_description(self, priority: PriorityLevel) -> str:
        """
        Get a human-readable description of a priority level.
        
        Args:
            priority (PriorityLevel): The priority level
            
        Returns:
            str: Description of the priority level
        """
        descriptions = {
            PriorityLevel.CRITICAL: "Critical - Must be addressed for security, compliance, or core functionality",
            PriorityLevel.HIGH: "High - Important for user experience and core features",
            PriorityLevel.MEDIUM: "Medium - Standard requirements for functionality",
            PriorityLevel.LOW: "Low - Nice to have or optional features"
        }
        return descriptions.get(priority, "Unknown priority level")
    
    def get_priority_color(self, priority: PriorityLevel) -> str:
        """
        Get a color code for a priority level (useful for UI).
        
        Args:
            priority (PriorityLevel): The priority level
            
        Returns:
            str: Color code (hex or CSS color name)
        """
        colors = {
            PriorityLevel.CRITICAL: "#dc3545",  # Red
            PriorityLevel.HIGH: "#fd7e14",      # Orange
            PriorityLevel.MEDIUM: "#ffc107",    # Yellow
            PriorityLevel.LOW: "#28a745"        # Green
        }
        return colors.get(priority, "#6c757d")  # Gray default
    
    def get_priority_icon(self, priority: PriorityLevel) -> str:
        """
        Get an icon representation for a priority level.
        
        Args:
            priority (PriorityLevel): The priority level
            
        Returns:
            str: Icon representation
        """
        icons = {
            PriorityLevel.CRITICAL: "🔴",
            PriorityLevel.HIGH: "🟠",
            PriorityLevel.MEDIUM: "🟡",
            PriorityLevel.LOW: "🟢"
        }
        return icons.get(priority, "⚪") 