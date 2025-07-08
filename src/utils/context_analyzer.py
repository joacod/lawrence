"""
Context Analyzer
Analyzes conversation history and user patterns to improve question generation.
"""
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re
from collections import Counter


@dataclass
class ContextInsight:
    """Insights derived from conversation context."""
    user_preferences: Dict[str, str]
    answered_topics: Set[str]
    pending_topics: Set[str]
    conversation_style: str
    detail_level: str
    technical_expertise: str
    feature_evolution: List[str]
    context_gaps: List[str]


@dataclass
class QuestionContext:
    """Context information for question generation."""
    feature_type: str
    conversation_history: List[Dict]
    answered_questions: List[Dict]
    pending_questions: List[Dict]
    user_insights: ContextInsight
    suggested_topics: List[str]
    avoid_topics: List[str]


class ContextAnalyzer:
    """
    Analyzes conversation context to improve question generation.
    
    Features:
    - User preference detection
    - Topic tracking and gap analysis
    - Conversation style analysis
    - Technical expertise assessment
    - Feature evolution tracking
    """
    
    def __init__(self):
        """Initialize the context analyzer."""
        self.topic_keywords = self._initialize_topic_keywords()
        self.style_indicators = self._initialize_style_indicators()
        self.expertise_indicators = self._initialize_expertise_indicators()
    
    def _initialize_topic_keywords(self) -> Dict[str, List[str]]:
        """Initialize topic keywords for categorization."""
        return {
            "security": [
                "security", "authentication", "authorization", "password", "login",
                "2fa", "two-factor", "encryption", "privacy", "gdpr", "compliance"
            ],
            "user_management": [
                "user", "account", "registration", "profile", "role", "permission",
                "admin", "moderator", "user type", "user group"
            ],
            "data_management": [
                "data", "database", "storage", "backup", "export", "import",
                "migration", "sync", "replication", "archive"
            ],
            "ui_ux": [
                "interface", "design", "layout", "ui", "ux", "user experience",
                "responsive", "mobile", "desktop", "theme", "customization"
            ],
            "performance": [
                "performance", "speed", "response time", "scalability", "load",
                "concurrent", "throughput", "optimization", "caching"
            ],
            "integration": [
                "api", "integration", "third-party", "external", "webhook",
                "synchronization", "connector", "plugin", "extension"
            ],
            "notifications": [
                "notification", "email", "sms", "push", "alert", "reminder",
                "communication", "messaging", "in-app"
            ],
            "reporting": [
                "report", "analytics", "dashboard", "metrics", "statistics",
                "insights", "kpi", "monitoring", "tracking"
            ],
            "workflow": [
                "workflow", "process", "approval", "status", "state", "transition",
                "automation", "business logic", "rules"
            ],
            "payment": [
                "payment", "billing", "subscription", "pricing", "invoice",
                "transaction", "gateway", "stripe", "paypal"
            ]
        }
    
    def _initialize_style_indicators(self) -> Dict[str, List[str]]:
        """Initialize conversation style indicators."""
        return {
            "detailed": [
                "specifically", "in detail", "comprehensive", "thorough",
                "complete", "full", "extensive", "detailed", "comprehensive"
            ],
            "concise": [
                "simple", "basic", "minimal", "essential", "core", "just",
                "only", "straightforward", "direct"
            ],
            "technical": [
                "api", "endpoint", "database", "schema", "architecture",
                "framework", "protocol", "algorithm", "optimization"
            ],
            "business": [
                "business", "user", "customer", "stakeholder", "requirement",
                "goal", "objective", "value", "benefit", "roi"
            ]
        }
    
    def _initialize_expertise_indicators(self) -> Dict[str, List[str]]:
        """Initialize technical expertise indicators."""
        return {
            "expert": [
                "microservices", "distributed", "scalable", "optimization",
                "performance", "security", "compliance", "architecture",
                "infrastructure", "devops"
            ],
            "intermediate": [
                "api", "database", "frontend", "backend", "integration",
                "authentication", "deployment", "testing", "monitoring"
            ],
            "beginner": [
                "simple", "basic", "easy", "user-friendly", "intuitive",
                "straightforward", "no technical knowledge", "plug-and-play"
            ]
        }
    
    def analyze_context(self, conversation_history: List[Dict], 
                       answered_questions: List[Dict],
                       pending_questions: List[Dict],
                       feature_type: str) -> ContextInsight:
        """
        Analyze conversation context to extract insights.
        
        Args:
            conversation_history (List[Dict]): List of conversation messages
            answered_questions (List[Dict]): List of answered questions
            pending_questions (List[Dict]): List of pending questions
            feature_type (str): The feature type
            
        Returns:
            ContextInsight: Extracted context insights
        """
        # Extract user messages
        user_messages = self._extract_user_messages(conversation_history)
        
        # Analyze user preferences
        user_preferences = self._analyze_user_preferences(user_messages)
        
        # Track answered and pending topics
        answered_topics = self._extract_topics_from_questions(answered_questions)
        pending_topics = self._extract_topics_from_questions(pending_questions)
        
        # Analyze conversation style
        conversation_style = self._analyze_conversation_style(user_messages)
        
        # Assess detail level
        detail_level = self._assess_detail_level(user_messages)
        
        # Assess technical expertise
        technical_expertise = self._assess_technical_expertise(user_messages)
        
        # Track feature evolution
        feature_evolution = self._track_feature_evolution(conversation_history)
        
        # Identify context gaps
        context_gaps = self._identify_context_gaps(
            answered_topics, pending_topics, feature_type
        )
        
        return ContextInsight(
            user_preferences=user_preferences,
            answered_topics=answered_topics,
            pending_topics=pending_topics,
            conversation_style=conversation_style,
            detail_level=detail_level,
            technical_expertise=technical_expertise,
            feature_evolution=feature_evolution,
            context_gaps=context_gaps
        )
    
    def _extract_user_messages(self, conversation_history: List[Dict]) -> List[str]:
        """Extract user messages from conversation history."""
        user_messages = []
        for message in conversation_history:
            if message.get('role') == 'user' or message.get('type') == 'human':
                content = message.get('content', '')
                if content:
                    user_messages.append(content)
        return user_messages
    
    def _analyze_user_preferences(self, user_messages: List[str]) -> Dict[str, str]:
        """Analyze user preferences from messages."""
        preferences = {}
        
        # Analyze preference patterns
        for message in user_messages:
            message_lower = message.lower()
            
            # Security preferences
            if any(word in message_lower for word in ['secure', 'security', 'protected']):
                if 'no security' in message_lower or 'minimal security' in message_lower:
                    preferences['security_level'] = 'minimal'
                elif 'high security' in message_lower or 'maximum security' in message_lower:
                    preferences['security_level'] = 'high'
                else:
                    preferences['security_level'] = 'standard'
            
            # UI preferences
            if any(word in message_lower for word in ['simple', 'basic', 'minimal']):
                preferences['ui_complexity'] = 'simple'
            elif any(word in message_lower for word in ['advanced', 'complex', 'detailed']):
                preferences['ui_complexity'] = 'advanced'
            else:
                preferences['ui_complexity'] = 'standard'
            
            # Integration preferences
            if any(word in message_lower for word in ['integrate', 'api', 'external']):
                preferences['integration_needs'] = 'yes'
            elif 'no integration' in message_lower or 'standalone' in message_lower:
                preferences['integration_needs'] = 'no'
        
        return preferences
    
    def _extract_topics_from_questions(self, questions: List[Dict]) -> Set[str]:
        """Extract topics from questions."""
        topics = set()
        
        for question in questions:
            question_text = question.get('question', '').lower()
            
            for topic, keywords in self.topic_keywords.items():
                if any(keyword in question_text for keyword in keywords):
                    topics.add(topic)
        
        return topics
    
    def _analyze_conversation_style(self, user_messages: List[str]) -> str:
        """Analyze the user's conversation style."""
        if not user_messages:
            return 'neutral'
        
        style_scores = Counter()
        
        for message in user_messages:
            message_lower = message.lower()
            
            for style, indicators in self.style_indicators.items():
                if any(indicator in message_lower for indicator in indicators):
                    style_scores[style] += 1
        
        if not style_scores:
            return 'neutral'
        
        # Return the most common style
        return style_scores.most_common(1)[0][0]
    
    def _assess_detail_level(self, user_messages: List[str]) -> str:
        """Assess the user's preferred detail level."""
        if not user_messages:
            return 'medium'
        
        detailed_count = 0
        concise_count = 0
        
        for message in user_messages:
            message_lower = message.lower()
            
            if any(indicator in message_lower for indicator in self.style_indicators['detailed']):
                detailed_count += 1
            elif any(indicator in message_lower for indicator in self.style_indicators['concise']):
                concise_count += 1
        
        if detailed_count > concise_count:
            return 'high'
        elif concise_count > detailed_count:
            return 'low'
        else:
            return 'medium'
    
    def _assess_technical_expertise(self, user_messages: List[str]) -> str:
        """Assess the user's technical expertise level."""
        if not user_messages:
            return 'intermediate'
        
        expertise_scores = Counter()
        
        for message in user_messages:
            message_lower = message.lower()
            
            for level, indicators in self.expertise_indicators.items():
                if any(indicator in message_lower for indicator in indicators):
                    expertise_scores[level] += 1
        
        if not expertise_scores:
            return 'intermediate'
        
        # Return the most common expertise level
        return expertise_scores.most_common(1)[0][0]
    
    def _track_feature_evolution(self, conversation_history: List[Dict]) -> List[str]:
        """Track how the feature has evolved through the conversation."""
        evolution = []
        
        for message in conversation_history:
            if message.get('role') == 'user' or message.get('type') == 'human':
                content = message.get('content', '')
                if content:
                    # Extract key changes or additions
                    if any(word in content.lower() for word in ['also', 'additionally', 'plus', 'and', 'also need']):
                        evolution.append(content[:100] + "...")
        
        return evolution
    
    def _identify_context_gaps(self, answered_topics: Set[str], 
                              pending_topics: Set[str], 
                              feature_type: str) -> List[str]:
        """Identify gaps in the conversation context."""
        gaps = []
        
        # Get expected topics for the feature type
        expected_topics = self._get_expected_topics_for_feature_type(feature_type)
        
        # Find missing topics
        covered_topics = answered_topics | pending_topics
        missing_topics = expected_topics - covered_topics
        
        for topic in missing_topics:
            gaps.append(f"Missing {topic} considerations")
        
        return gaps
    
    def _get_expected_topics_for_feature_type(self, feature_type: str) -> Set[str]:
        """Get expected topics for a given feature type."""
        expected_topics = {
            "authentication": {"security", "user_management", "data_management"},
            "payment": {"payment", "security", "data_management", "integration"},
            "crud": {"data_management", "ui_ux", "performance", "user_management"},
            "integration": {"integration", "performance", "data_management"},
            "workflow": {"workflow", "user_management", "notifications", "ui_ux"},
            "reporting": {"reporting", "data_management", "ui_ux", "performance"},
            "notification": {"notifications", "user_management", "integration"},
            "search": {"performance", "ui_ux", "data_management"},
            "ui": {"ui_ux", "performance", "user_management"},
            "general": {"user_management", "ui_ux", "data_management"}
        }
        
        return expected_topics.get(feature_type, {"user_management", "ui_ux"})
    
    def generate_contextual_questions(self, context_insight: ContextInsight,
                                    feature_type: str,
                                    current_questions: List[str]) -> List[str]:
        """
        Generate contextual questions based on conversation insights.
        
        Args:
            context_insight (ContextInsight): Analyzed context insights
            feature_type (str): The feature type
            current_questions (List[str]): Current questions to avoid duplicates
            
        Returns:
            List[str]: Generated contextual questions
        """
        contextual_questions = []
        
        # Generate questions based on context gaps
        for gap in context_insight.context_gaps:
            question = self._generate_gap_question(gap, context_insight)
            if question and question not in current_questions:
                contextual_questions.append(question)
        
        # Generate questions based on user preferences
        preference_questions = self._generate_preference_questions(context_insight)
        for question in preference_questions:
            if question not in current_questions:
                contextual_questions.append(question)
        
        # Generate questions based on conversation style
        style_questions = self._generate_style_questions(context_insight)
        for question in style_questions:
            if question not in current_questions:
                contextual_questions.append(question)
        
        return contextual_questions[:3]  # Limit to 3 contextual questions
    
    def _generate_gap_question(self, gap: str, context_insight: ContextInsight) -> Optional[str]:
        """Generate a question to address a context gap."""
        gap_lower = gap.lower()
        
        if "security" in gap_lower:
            if context_insight.technical_expertise == "expert":
                return "What specific security measures and compliance requirements should be implemented?"
            else:
                return "Are there any security considerations we should address?"
        
        elif "performance" in gap_lower:
            if context_insight.detail_level == "high":
                return "What are the expected performance requirements and scalability needs?"
            else:
                return "Are there any performance considerations we should keep in mind?"
        
        elif "integration" in gap_lower:
            if context_insight.user_preferences.get('integration_needs') == 'yes':
                return "Which external systems or APIs need to be integrated?"
            else:
                return "Will this feature need to integrate with any other systems?"
        
        elif "user management" in gap_lower:
            return "Who are the primary users and what roles or permissions are needed?"
        
        elif "data management" in gap_lower:
            return "What data will be stored and how should it be managed?"
        
        return None
    
    def _generate_preference_questions(self, context_insight: ContextInsight) -> List[str]:
        """Generate questions based on user preferences."""
        questions = []
        
        # Security preference questions
        security_level = context_insight.user_preferences.get('security_level')
        if security_level == 'minimal':
            questions.append("Are you comfortable with basic authentication, or do you need additional security measures?")
        elif security_level == 'high':
            questions.append("What specific security requirements and compliance standards need to be met?")
        
        # UI preference questions
        ui_complexity = context_insight.user_preferences.get('ui_complexity')
        if ui_complexity == 'simple':
            questions.append("Should the interface be kept simple and minimal, or do you need advanced features?")
        elif ui_complexity == 'advanced':
            questions.append("What advanced UI features and customizations are required?")
        
        return questions
    
    def _generate_style_questions(self, context_insight: ContextInsight) -> List[str]:
        """Generate questions based on conversation style."""
        questions = []
        
        if context_insight.conversation_style == 'technical':
            questions.append("What technical specifications and implementation details should be considered?")
        elif context_insight.conversation_style == 'business':
            questions.append("What are the business goals and success metrics for this feature?")
        elif context_insight.conversation_style == 'detailed':
            questions.append("Are there any specific requirements or edge cases we should address?")
        
        return questions
    
    def get_question_context(self, conversation_history: List[Dict],
                           answered_questions: List[Dict],
                           pending_questions: List[Dict],
                           feature_type: str) -> QuestionContext:
        """
        Get comprehensive context for question generation.
        
        Args:
            conversation_history (List[Dict]): Conversation history
            answered_questions (List[Dict]): Answered questions
            pending_questions (List[Dict]): Pending questions
            feature_type (str): Feature type
            
        Returns:
            QuestionContext: Comprehensive context for question generation
        """
        # Analyze context
        user_insights = self.analyze_context(
            conversation_history, answered_questions, pending_questions, feature_type
        )
        
        # Generate contextual questions
        contextual_questions = self.generate_contextual_questions(
            user_insights, feature_type, [q.get('question', '') for q in pending_questions]
        )
        
        # Determine topics to avoid (already covered)
        avoid_topics = list(user_insights.answered_topics)
        
        return QuestionContext(
            feature_type=feature_type,
            conversation_history=conversation_history,
            answered_questions=answered_questions,
            pending_questions=pending_questions,
            user_insights=user_insights,
            suggested_topics=contextual_questions,
            avoid_topics=avoid_topics
        ) 