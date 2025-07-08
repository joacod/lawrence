"""
PO Agent
Product Owner agent for feature clarification and documentation.
Uses the base agent framework with conversation history support.
"""
from typing import List, Dict
import json
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, AIMessage
# parse_response_to_json no longer needed - base agent handles parsing automatically
from src.utils.parsers.question_parser import parse_questions_section
from src.utils.parsers.markdown_parser import extract_title_from_markdown
from src.core.session_manager import SessionManager
from src.agents.question_analysis_agent import QuestionAnalysisAgent
from src.config.settings import settings
from src.utils.feature_classifier import FeatureTypeClassifier
from src.utils.question_prioritizer import QuestionPrioritizer
from src.utils.context_analyzer import ContextAnalyzer
from src.utils.question_processor import QuestionProcessor
from .base import ConversationalAgent

class POAgent(ConversationalAgent):
    """
    Product Owner Agent for feature clarification and documentation.
    
    Features:
    - Automatic configuration from AgentConfigRegistry
    - Built-in retry logic and error handling
    - Conversation history support
    - Session management integration
    - Intent classification for follow-ups
    """
    
    def __init__(self):
        """Initialize POAgent with 'po' configuration."""
        super().__init__(agent_type="po")
        self.session_manager = SessionManager()
        self.question_analysis_agent = QuestionAnalysisAgent()
        self.feature_classifier = FeatureTypeClassifier()
        self.question_prioritizer = QuestionPrioritizer()
        self.context_analyzer = ContextAnalyzer()
        self.question_processor = QuestionProcessor()

    def _classify_user_intent(self, user_input: str, existing_questions: List[dict]) -> str:
        """
        Classify user intent to determine if this is a new feature or follow-up.
        
        Args:
            user_input (str): The user's input
            existing_questions (List[dict]): Existing questions in the session
            
        Returns:
            str: 'new_feature', 'question_answer', or 'clarification'
        """
        # Simple heuristics for intent classification
        input_lower = user_input.lower()
        
        # Check if input looks like an answer to a specific question
        if existing_questions:
            # Look for patterns that suggest answering specific questions
            answer_indicators = [
                'more than', 'at least', 'minimum', 'maximum', 'between',
                'yes', 'no', 'not', 'never', 'always', 'only', 'just',
                'characters', 'uppercase', 'lowercase', 'numbers', 'special',
                'attempts', 'wait', 'hour', 'minutes', 'seconds',
                'email', 'password', 'username', 'login', 'register'
            ]
            
            # If input contains specific answer patterns and there are pending questions
            if any(indicator in input_lower for indicator in answer_indicators):
                return 'question_answer'
        
        # Check if input looks like a new feature description
        new_feature_indicators = [
            'i want', 'i need', 'create', 'build', 'implement', 'add',
            'feature', 'system', 'application', 'website', 'app'
        ]
        
        if any(indicator in input_lower for indicator in new_feature_indicators):
            return 'new_feature'
        
        # Default to question answer if there are existing questions
        return 'question_answer' if existing_questions else 'new_feature'

    def _find_matching_question(self, user_input: str, pending_questions: List[dict]) -> dict | None:
        """
        Find the most likely question the user is answering.
        
        Args:
            user_input (str): The user's input
            pending_questions (List[dict]): List of pending questions
            
        Returns:
            dict | None: The matching question or None
        """
        input_lower = user_input.lower()
        
        # Simple keyword matching for now - could be enhanced with semantic similarity
        for question in pending_questions:
            question_text = question.get('question', '').lower()
            
            # Check for password complexity related keywords
            if any(keyword in question_text for keyword in ['password', 'complexity', 'rules', 'length', 'characters']):
                if any(keyword in input_lower for keyword in ['character', 'uppercase', 'lowercase', 'number', 'special', 'minimum', 'maximum']):
                    return question
            
            # Check for security measures
            if any(keyword in question_text for keyword in ['security', 'two-factor', '2fa', 'captcha', 'authentication']):
                if any(keyword in input_lower for keyword in ['attempt', 'wait', 'hour', 'lock', 'block']):
                    return question
            
            # Check for registration
            if any(keyword in question_text for keyword in ['register', 'account', 'existing']):
                if any(keyword in input_lower for keyword in ['register', 'account', 'email']):
                    return question
            
            # Check for password reset
            if any(keyword in question_text for keyword in ['forgotten', 'reset', 'recovery']):
                if any(keyword in input_lower for keyword in ['reset', 'forgot', 'recovery', 'email']):
                    return question
        
        return None

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str, str, list, int, int, datetime, datetime]:
        """
        Process a feature request and return comprehensive response data.
        
        Args:
            feature (str): The feature description
            session_id (str | None): Optional session ID
            
        Returns:
            tuple: (session_id, title, response, markdown, questions, total_questions, answered_questions, created_at, updated_at)
        """
        session_id = self.session_manager.create_session(session_id)
        created_at, updated_at = self.session_manager.get_session_timestamps(session_id)
        chat_history = self.session_manager.get_chat_history(session_id)

        # Detect feature type for new features
        existing_questions = self.session_manager.get_questions(session_id)
        is_followup = len(existing_questions) > 0 and len(chat_history) > 0
        
        if not is_followup:
            # For new features, detect the feature type
            feature_type = self._detect_feature_type(feature)
            self.session_manager.set_session_feature_type(session_id, feature_type)
            self.logger.info(f"New feature detected as type: {feature_type}")
        else:
            # For follow-ups, use existing feature type
            feature_type = self.session_manager.get_session_feature_type(session_id)
        
        if is_followup:
            self.logger.info("Processing follow-up response to existing questions")
            
            # Classify user intent
            intent = self._classify_user_intent(feature, existing_questions)
            self.logger.info(f"Classified user intent as: {intent}")
            
            if intent == 'question_answer':
                # Find the most likely question being answered
                matching_question = self._find_matching_question(feature, existing_questions)
                
                if matching_question:
                    self.logger.info(f"Found matching question: {matching_question.get('question', '')[:50]}...")
                    # Directly answer the specific question
                    self.session_manager.answer_question(session_id, matching_question['question'], feature)
                else:
                    # Use QuestionAnalysisAgent to analyze all pending questions with context
                    pending_questions = self.session_manager.get_pending_questions(session_id)
                    if pending_questions:
                        # Get conversation context and previous Q&A
                        conversation_context = self._get_conversation_context(chat_history)
                        answered_questions = [q for q in existing_questions if q["status"] in ("answered", "disregarded")]
                        
                        analysis_markdown = await self.question_analysis_agent.analyze(
                            pending_questions, feature, conversation_context, answered_questions
                        )
                        analysis = parse_questions_section(analysis_markdown)
                        for result in analysis:
                            q_text = result.get("question")
                            status = result.get("status")
                            user_answer = result.get("user_answer")
                            if status == "answered":
                                self.session_manager.answer_question(session_id, q_text, user_answer or feature)
                            elif status == "disregarded":
                                self.session_manager.disregard_question(session_id, q_text)

        try:
            self.logger.info("Getting conversational response from model")
            
            # Use the base agent's invoke method with automatic retry handling
            # Include feature type information in the input
            feature_input = f"FEATURE TYPE: {feature_type}\n\nUSER INPUT: {feature}"
            output = await self.invoke({
                "chat_history": chat_history,
                "input": feature_input
            })

            # Handle questions using unified processor for optimal performance
            new_questions = output.get("questions", [])
            if new_questions:
                if isinstance(new_questions[0], str):
                    # Use unified processor for optimal performance
                    processed_questions = await self._process_questions_unified(new_questions, session_id, feature_type)
                    
                    if is_followup:
                        # For follow-ups, add new questions to existing ones
                        self.session_manager.add_questions_with_priorities(session_id, processed_questions)
                    else:
                        # For new features, set the questions
                        self.session_manager.set_questions(session_id, processed_questions)
                elif isinstance(new_questions[0], dict):
                    # Handle case where questions are already in dict format
                    if is_followup:
                        # Add only questions that don't already exist
                        existing_question_texts = {q['question'] for q in existing_questions}
                        questions_to_add = []
                        for new_q in new_questions:
                            if new_q.get('question') not in existing_question_texts:
                                questions_to_add.append(new_q)
                        
                        if questions_to_add:
                            self.session_manager.add_questions_with_priorities(session_id, questions_to_add)
                    else:
                        self.session_manager.set_questions(session_id, new_questions)

            # Always include all questions with their status and user_answer, ordered by priority
            all_questions = self.session_manager.get_questions_ordered_by_priority(session_id)
            output["questions"] = all_questions

            # Calculate progress
            total_questions = len(all_questions)
            answered_questions = sum(1 for q in all_questions if q["status"] in ("answered", "disregarded"))

            # Extract title from markdown if this is a new session
            title = self._extract_title_from_markdown(output["markdown"], session_id)
            
            # Update chat history
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            self.session_manager.update_chat_history(session_id, chat_history)
            
            return session_id, title, output["response"], output["markdown"], output["questions"], total_questions, answered_questions, created_at, updated_at
            
        except Exception as e:
            self.logger.error("Error in process_feature:", exc_info=True)
            self.logger.error(f"Session ID: {session_id}")
            self.logger.error(f"Feature input: {feature}")
            raise

    def _get_conversation_context(self, chat_history: List) -> str:
        """Extract recent conversation context for question analysis."""
        if not chat_history:
            return ""
        
        # Get the last few messages for context (limit to avoid token limits)
        recent_messages = chat_history[-6:]  # Last 3 exchanges (6 messages)
        context_parts = []
        
        for message in recent_messages:
            if hasattr(message, 'content'):
                # Truncate long messages
                content = str(message.content)[:200]
                context_parts.append(f"{type(message).__name__}: {content}")
        
        return "\n".join(context_parts)

    def _detect_feature_type(self, feature_description: str) -> str:
        """
        Detect the feature type using the feature classifier.
        
        Args:
            feature_description (str): The feature description to classify
            
        Returns:
            str: The detected feature type
        """
        classification = self.feature_classifier.classify(feature_description)
        self.logger.info(f"Feature type detected: {classification.primary_type} (confidence: {classification.confidence:.2f})")
        return classification.primary_type
    
    def _prioritize_questions(self, questions: List[str], feature_type: str) -> List[Dict]:
        """
        Prioritize questions using the question prioritizer.
        
        Args:
            questions (List[str]): List of questions to prioritize
            feature_type (str): The feature type for context
            
        Returns:
            List[Dict]: List of questions with priority information
        """
        if not questions:
            return []
        
        # Get prioritized questions
        prioritized_questions = self.question_prioritizer.prioritize_questions(questions, feature_type)
        
        # Convert to dictionary format for session manager
        questions_with_priorities = []
        for pq in prioritized_questions:
            questions_with_priorities.append({
                'question': pq.question,
                'feature_type': feature_type,
                'priority': pq.priority.value,
                'priority_score': pq.score,
                'priority_reasoning': pq.reasoning
            })
        
        self.logger.info(f"Prioritized {len(questions_with_priorities)} questions for {feature_type} feature")
        return questions_with_priorities
    
    async def _process_questions_unified(self, questions: List[str], session_id: str, feature_type: str) -> List[Dict]:
        """
        Process questions using the unified processor for optimal performance.
        
        Args:
            questions (List[str]): Raw questions from LLM
            session_id (str): Session ID for caching
            feature_type (str): Detected feature type
            
        Returns:
            List[Dict]: Processed questions with all metadata
        """
        # Get conversation history and questions
        chat_history = self.session_manager.get_chat_history(session_id)
        all_questions = self.session_manager.get_questions(session_id)
        answered_questions = [q for q in all_questions if q["status"] in ("answered", "disregarded")]
        pending_questions = [q for q in all_questions if q["status"] == "pending"]
        
        # Convert chat history to the format expected by processor
        conversation_history = []
        for message in chat_history:
            if hasattr(message, 'content'):
                message_type = 'human' if hasattr(message, '__class__') and 'Human' in message.__class__.__name__ else 'ai'
                conversation_history.append({
                    'type': message_type,
                    'content': str(message.content)
                })
        
        # Process questions using unified processor
        processed_result = await self.question_processor.process_questions(
            questions=questions,
            conversation_history=conversation_history,
            answered_questions=answered_questions,
            pending_questions=pending_questions,
            session_id=session_id
        )
        
        self.logger.info(f"Unified processing completed in {processed_result.processing_time:.3f}s")
        self.logger.info(f"Generated {processed_result.total_questions} questions ({processed_result.contextual_count} contextual)")
        
        return processed_result.questions
    
    def _get_enhanced_context(self, session_id: str, feature_type: str) -> Dict:
        """
        Get enhanced context for question generation.
        
        Args:
            session_id (str): The session ID
            feature_type (str): The feature type
            
        Returns:
            Dict: Enhanced context information
        """
        # Get conversation history
        chat_history = self.session_manager.get_chat_history(session_id)
        
        # Convert chat history to the format expected by context analyzer
        conversation_history = []
        for message in chat_history:
            if hasattr(message, 'content'):
                message_type = 'human' if hasattr(message, '__class__') and 'Human' in message.__class__.__name__ else 'ai'
                conversation_history.append({
                    'type': message_type,
                    'content': str(message.content)
                })
        
        # Get answered and pending questions
        all_questions = self.session_manager.get_questions(session_id)
        answered_questions = [q for q in all_questions if q["status"] in ("answered", "disregarded")]
        pending_questions = [q for q in all_questions if q["status"] == "pending"]
        
        # Get context insights
        context_insight = self.context_analyzer.analyze_context(
            conversation_history, answered_questions, pending_questions, feature_type
        )
        
        # Generate contextual questions
        contextual_questions = self.context_analyzer.generate_contextual_questions(
            context_insight, feature_type, [q.get('question', '') for q in pending_questions]
        )
        
        self.logger.info(f"Generated {len(contextual_questions)} contextual questions based on conversation analysis")
        
        return {
            'context_insight': context_insight,
            'contextual_questions': contextual_questions,
            'conversation_history': conversation_history,
            'answered_questions': answered_questions,
            'pending_questions': pending_questions
        }

    def _extract_title_from_markdown(self, markdown: str, session_id: str) -> str:
        """Extract title from markdown and set it for the session"""
        # Check if session already has a title
        existing_title = self.session_manager.get_session_title(session_id)
        if existing_title != "Untitled Feature":
            return existing_title
        
        # Use the dedicated markdown parser
        title = extract_title_from_markdown(markdown)
        
        # Set the title for this session
        self.session_manager.set_session_title(session_id, title)
        return title
    
    async def process(self, feature: str, session_id: str | None = None) -> tuple:
        """Main processing method - delegates to process_feature."""
        return await self.process_feature(feature, session_id)

    def _is_similar_question(self, new_question: str, existing_questions: List[dict]) -> bool:
        """
        Check if a new question is similar to existing questions.
        
        Args:
            new_question (str): The new question to check
            existing_questions (List[dict]): List of existing questions
            
        Returns:
            bool: True if similar question exists, False otherwise
        """
        new_question_lower = new_question.lower()
        
        # Enhanced keywords to check for similarity with more granular categories
        similarity_keywords = {
            '2fa': ['two factor', 'two-factor', '2fa', 'authentication', 'additional authentication'],
            'password_reset': ['forgotten password', 'password reset', 'password recovery', 'reset password', 'forgot password'],
            'registration': ['register', 'registration', 'sign up', 'account creation', 'new account'],
            'password_complexity': [
                'password complexity', 'password rules', 'password requirements', 'minimum length', 
                'special characters', 'uppercase', 'lowercase', 'numbers', 'characters', 'password strength'
            ],
            'password_attempts': [
                'wrong password', 'incorrect password', 'failed attempts', 'attempts', 'wrong attempts',
                'lock account', 'lockout', 'brute force', 'wait', 'hour', 'minutes', 'block'
            ],
            'security': ['security measures', 'security', 'protection', 'lock', 'secure'],
            'email': ['email verification', 'email link', 'email code', 'email reset', 'email'],
            'user_management': ['user', 'account', 'profile', 'user type', 'role']
        }
        
        for category, keywords in similarity_keywords.items():
            # Check if new question contains any keywords from this category
            new_has_keywords = any(keyword in new_question_lower for keyword in keywords)
            
            if new_has_keywords:
                # Check if any existing question has similar keywords
                for existing_q in existing_questions:
                    existing_text = existing_q.get('question', '').lower()
                    existing_has_keywords = any(keyword in existing_text for keyword in keywords)
                    
                    if existing_has_keywords:
                        # Check if the existing question is already answered
                        if existing_q.get('status') == 'answered':
                            # If the existing question is answered and covers the same topic,
                            # the new question is redundant
                            if self._are_questions_about_same_topic(new_question_lower, existing_text):
                                return True
                        else:
                            # If the existing question is pending, check if they're asking the same thing
                            if self._are_questions_about_same_topic(new_question_lower, existing_text):
                                return True
        
        return False
    
    def _are_questions_about_same_topic(self, question1: str, question2: str) -> bool:
        """
        Check if two questions are about the same topic.
        
        Args:
            question1 (str): First question (lowercase)
            question2 (str): Second question (lowercase)
            
        Returns:
            bool: True if questions are about the same topic
        """
        # Extract key topic words from questions with more granular detection
        def extract_topics(question: str) -> set:
            topics = set()
            
            # Authentication topics
            if any(word in question for word in ['2fa', 'two factor', 'authentication', 'additional authentication']):
                topics.add('2fa')
            
            # Password reset topics
            if any(word in question for word in ['password reset', 'forgotten password', 'forgot password', 'password recovery']):
                topics.add('password_reset')
            
            # Registration topics
            if any(word in question for word in ['register', 'registration', 'sign up', 'account creation']):
                topics.add('registration')
            
            # Password complexity topics
            if any(word in question for word in ['password complexity', 'password rules', 'password requirements', 'minimum length', 'special characters', 'uppercase', 'lowercase', 'numbers']):
                topics.add('password_complexity')
            
            # Password attempts/security topics
            if any(word in question for word in ['wrong password', 'incorrect password', 'failed attempts', 'attempts', 'lock account', 'lockout', 'brute force', 'wait', 'hour']):
                topics.add('password_attempts')
            
            # General security topics
            if 'security' in question:
                topics.add('security')
            
            # Email topics
            if 'email' in question:
                topics.add('email')
            
            # User management topics
            if any(word in question for word in ['user', 'account', 'profile', 'role']):
                topics.add('user_management')
            
            return topics
        
        topics1 = extract_topics(question1)
        topics2 = extract_topics(question2)
        
        # If they share any topic, they're about the same subject
        return bool(topics1 & topics2)

    def _filter_duplicate_questions(self, new_questions: List, existing_questions: List[dict]) -> List:
        """
        Filter out questions that are similar to existing ones.
        
        Args:
            new_questions (List): List of new questions (strings or dicts)
            existing_questions (List[dict]): List of existing questions
            
        Returns:
            List: Filtered list of new questions without duplicates
        """
        filtered_questions = []
        
        for new_q in new_questions:
            if isinstance(new_q, str):
                question_text = new_q
            elif isinstance(new_q, dict):
                question_text = new_q.get('question', '')
            else:
                continue
            
            # Check if this question is similar to existing ones
            if not self._is_similar_question(question_text, existing_questions):
                # Additional check: ensure the question hasn't been answered in recent user input
                if not self._is_question_already_answered(question_text, existing_questions):
                    filtered_questions.append(new_q)
                else:
                    self.logger.info(f"Filtered out already answered question: {question_text[:50]}...")
            else:
                self.logger.info(f"Filtered out duplicate question: {question_text[:50]}...")
        
        return filtered_questions
    
    def _is_question_already_answered(self, question_text: str, existing_questions: List[dict]) -> bool:
        """
        Check if a question has already been answered by the user.
        
        Args:
            question_text (str): The question to check
            existing_questions (List[dict]): List of existing questions
            
        Returns:
            bool: True if the question has already been answered
        """
        question_lower = question_text.lower()
        
        # Check if any answered question covers the same topic
        for existing_q in existing_questions:
            if existing_q.get('status') == 'answered':
                existing_text = existing_q.get('question', '').lower()
                
                # If they're about the same topic and the existing one is answered
                if self._are_questions_about_same_topic(question_lower, existing_text):
                    return True
        
        return False 