"""
Question Processor
Unified processor that integrates feature classification, prioritization, and context analysis.
Optimized for performance and consistency.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.utils.feature_classifier import FeatureTypeClassifier
from src.utils.question_prioritizer import QuestionPrioritizer, QuestionPriority
from src.utils.context_analyzer import ContextAnalyzer, ContextInsight


@dataclass
class ProcessedQuestions:
    """Result of question processing with all metadata."""
    questions: List[Dict]
    feature_type: str
    context_insights: Optional[ContextInsight]
    processing_time: float
    total_questions: int
    prioritized_count: int
    contextual_count: int


class QuestionProcessor:
    """
    Unified processor for question generation, prioritization, and context analysis.
    
    Features:
    - Integrated feature classification, prioritization, and context analysis
    - Performance optimization with caching and parallel processing
    - Consistent question format and metadata
    - Comprehensive logging and monitoring
    """
    
    def __init__(self, max_workers: int = 4):
        """Initialize the question processor with optimized components."""
        self.feature_classifier = FeatureTypeClassifier()
        self.question_prioritizer = QuestionPrioritizer()
        self.context_analyzer = ContextAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._cache = {}  # Simple cache for feature type classification
        
    async def process_questions(self, 
                              questions: List[str],
                              conversation_history: List[Dict],
                              answered_questions: List[Dict],
                              pending_questions: List[Dict],
                              session_id: str) -> ProcessedQuestions:
        """
        Process questions with full integration of all features.
        
        Args:
            questions (List[str]): Raw questions from LLM
            conversation_history (List[Dict]): Conversation history
            answered_questions (List[Dict]): Previously answered questions
            pending_questions (List[Dict]): Current pending questions
            session_id (str): Session ID for caching
            
        Returns:
            ProcessedQuestions: Fully processed questions with metadata
        """
        start_time = datetime.now()
        
        # Step 1: Detect feature type (with caching)
        feature_type = await self._get_feature_type_cached(conversation_history, session_id)
        
        # Step 2: Analyze context (parallel with feature classification)
        context_task = asyncio.create_task(
            self._analyze_context_async(conversation_history, answered_questions, pending_questions, feature_type)
        )
        
        # Step 3: Filter and deduplicate questions
        filtered_questions = self._filter_questions(questions, answered_questions, pending_questions)
        
        # Step 4: Generate contextual questions
        context_insight = await context_task
        contextual_questions = self._generate_contextual_questions(context_insight, feature_type, filtered_questions)
        
        # Step 5: Combine and prioritize all questions
        all_questions = filtered_questions + contextual_questions
        prioritized_questions = self._prioritize_questions(all_questions, feature_type)
        
        # Step 6: Convert to final format
        final_questions = self._format_questions(prioritized_questions, feature_type, context_insight)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessedQuestions(
            questions=final_questions,
            feature_type=feature_type,
            context_insights=context_insight,
            processing_time=processing_time,
            total_questions=len(final_questions),
            prioritized_count=len(prioritized_questions),
            contextual_count=len(contextual_questions)
        )
    
    async def _get_feature_type_cached(self, conversation_history: List[Dict], session_id: str) -> str:
        """Get feature type with caching for performance."""
        cache_key = f"{session_id}_feature_type"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Extract feature description from conversation
        feature_description = self._extract_feature_description(conversation_history)
        
        # Run feature classification in thread pool
        loop = asyncio.get_event_loop()
        feature_type = await loop.run_in_executor(
            self.executor, 
            self.feature_classifier.classify, 
            feature_description
        )
        
        # Cache the result
        self._cache[cache_key] = feature_type.primary_type
        return feature_type.primary_type
    
    def _extract_feature_description(self, conversation_history: List[Dict]) -> str:
        """Extract feature description from conversation history."""
        if not conversation_history:
            return ""
        
        # Get the first user message (usually the feature description)
        for message in conversation_history:
            if message.get('type') == 'human' or message.get('role') == 'user':
                return message.get('content', '')
        
        return ""
    
    async def _analyze_context_async(self, conversation_history: List[Dict],
                                   answered_questions: List[Dict],
                                   pending_questions: List[Dict],
                                   feature_type: str) -> ContextInsight:
        """Analyze context asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.context_analyzer.analyze_context,
            conversation_history,
            answered_questions,
            pending_questions,
            feature_type
        )
    
    def _filter_questions(self, questions: List[str], 
                         answered_questions: List[Dict],
                         pending_questions: List[Dict]) -> List[str]:
        """Filter out duplicate and already-answered questions."""
        filtered = []
        existing_questions = answered_questions + pending_questions
        
        # Handle None or empty questions
        if not questions:
            return filtered
        
        for question in questions:
            # Skip None or empty questions
            if not question or not isinstance(question, str):
                continue
                
            if not self._is_duplicate_or_answered(question, existing_questions):
                filtered.append(question)
        
        return filtered
    
    def _is_duplicate_or_answered(self, question: str, existing_questions: List[Dict]) -> bool:
        """Check if question is duplicate or already answered."""
        question_lower = question.lower()
        
        for existing_q in existing_questions:
            existing_text = existing_q.get('question', '').lower()
            
            # Check for exact duplicates
            if question_lower == existing_text:
                return True
            
            # Check for semantic duplicates
            if self._are_semantically_similar(question_lower, existing_text):
                return True
            
            # Check if already answered
            if existing_q.get('status') == 'answered':
                if self._are_semantically_similar(question_lower, existing_text):
                    return True
        
        return False
    
    def _are_semantically_similar(self, question1: str, question2: str) -> bool:
        """Check if two questions are semantically similar."""
        # Use the same logic as in PO Agent but optimized
        similarity_keywords = {
            'password_complexity': ['password complexity', 'password rules', 'minimum length', 'special characters'],
            'password_attempts': ['wrong password', 'failed attempts', 'lock account', 'brute force'],
            'security': ['security', 'authentication', 'protection'],
            'registration': ['register', 'sign up', 'account creation'],
            'password_reset': ['password reset', 'forgot password', 'password recovery']
        }
        
        for category, keywords in similarity_keywords.items():
            q1_has_keywords = any(keyword in question1 for keyword in keywords)
            q2_has_keywords = any(keyword in question2 for keyword in keywords)
            
            if q1_has_keywords and q2_has_keywords:
                return True
        
        return False
    
    def _generate_contextual_questions(self, context_insight: ContextInsight,
                                     feature_type: str,
                                     existing_questions: List[str]) -> List[str]:
        """Generate contextual questions based on insights."""
        return self.context_analyzer.generate_contextual_questions(
            context_insight, feature_type, existing_questions
        )
    
    def _prioritize_questions(self, questions: List[str], feature_type: str) -> List[QuestionPriority]:
        """Prioritize questions using the prioritizer."""
        return self.question_prioritizer.prioritize_questions(questions, feature_type)
    
    def _format_questions(self, prioritized_questions: List[QuestionPriority],
                         feature_type: str,
                         context_insight: Optional[ContextInsight]) -> List[Dict]:
        """Format questions for session storage."""
        formatted_questions = []
        
        for pq in prioritized_questions:
            question_data = {
                'question': pq.question,
                'status': 'pending',
                'user_answer': None,
                'feature_type': feature_type,
                'priority': pq.priority.value,
                'priority_score': pq.score,
                'priority_reasoning': pq.reasoning,
                'created_at': datetime.now().isoformat()
            }
            
            # Add context metadata if available
            if context_insight:
                question_data['context_metadata'] = {
                    'user_expertise': context_insight.technical_expertise,
                    'conversation_style': context_insight.conversation_style,
                    'detail_level': context_insight.detail_level
                }
            
            formatted_questions.append(question_data)
        
        return formatted_questions
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics for monitoring."""
        return {
            'cache_size': len(self._cache),
            'executor_workers': self.executor._max_workers,
            'components': {
                'feature_classifier': 'active',
                'question_prioritizer': 'active',
                'context_analyzer': 'active'
            }
        }
    
    def clear_cache(self) -> None:
        """Clear the feature type cache."""
        self._cache.clear()
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 