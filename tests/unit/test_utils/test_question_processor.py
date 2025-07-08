import pytest
import asyncio
from unittest.mock import Mock, patch
from src.utils.question_processor import QuestionProcessor, ProcessedQuestions


class TestQuestionProcessor:
    """Test the QuestionProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a question processor instance for testing."""
        return QuestionProcessor(max_workers=2)
    
    def test_initialization(self, processor):
        """Test that the processor initializes correctly."""
        assert processor is not None
        assert hasattr(processor, 'feature_classifier')
        assert hasattr(processor, 'question_prioritizer')
        assert hasattr(processor, 'context_analyzer')
        assert hasattr(processor, 'executor')
        assert hasattr(processor, '_cache')
        assert processor.executor._max_workers == 2
    
    def test_extract_feature_description(self, processor):
        """Test extraction of feature description from conversation history."""
        conversation_history = [
            {'type': 'human', 'content': 'I need a login system'},
            {'type': 'ai', 'content': 'I understand'},
            {'type': 'human', 'content': 'With two-factor authentication'}
        ]
        
        description = processor._extract_feature_description(conversation_history)
        assert description == 'I need a login system'
    
    def test_extract_feature_description_empty(self, processor):
        """Test extraction with empty conversation history."""
        description = processor._extract_feature_description([])
        assert description == ""
    
    def test_is_duplicate_or_answered(self, processor):
        """Test duplicate and answered question detection."""
        existing_questions = [
            {
                'question': 'What security measures are required?',
                'status': 'answered',
                'user_answer': 'Two-factor authentication'
            },
            {
                'question': 'How should the interface be designed?',
                'status': 'pending',
                'user_answer': None
            }
        ]
        
        # Test exact duplicate
        assert processor._is_duplicate_or_answered(
            'What security measures are required?', existing_questions
        )
        
        # Test semantic duplicate (already answered)
        assert processor._is_duplicate_or_answered(
            'What security features do we need?', existing_questions
        )
        
        # Test new question
        assert not processor._is_duplicate_or_answered(
            'What database should we use?', existing_questions
        )
    
    def test_are_semantically_similar(self, processor):
        """Test semantic similarity detection."""
        # Test password complexity questions
        assert processor._are_semantically_similar(
            'What password rules should we have?',
            'What are the password complexity requirements?'
        )
        
        # Test password attempts questions
        assert processor._are_semantically_similar(
            'What happens after wrong password attempts?',
            'How many failed attempts before lockout?'
        )
        
        # Test different topics
        assert not processor._are_semantically_similar(
            'What password rules should we have?',
            'What database should we use?'
        )
    
    def test_filter_questions(self, processor):
        """Test question filtering."""
        questions = [
            'What security measures are required?',
            'How should the interface be designed?',
            'What database should we use?'
        ]
        
        answered_questions = [
            {
                'question': 'What security measures are required?',
                'status': 'answered',
                'user_answer': 'Two-factor authentication'
            }
        ]
        
        pending_questions = [
            {
                'question': 'How should the interface be designed?',
                'status': 'pending',
                'user_answer': None
            }
        ]
        
        filtered = processor._filter_questions(questions, answered_questions, pending_questions)
        
        # Should filter out the answered security question and pending interface question
        assert len(filtered) == 1
        assert 'database' in filtered[0]
    
    def test_format_questions(self, processor):
        """Test question formatting."""
        from src.utils.question_prioritizer import QuestionPriority, PriorityLevel
        
        prioritized_questions = [
            QuestionPriority(
                question='What security measures are required?',
                priority=PriorityLevel.CRITICAL,
                score=3.5,
                reasoning='Security keywords detected'
            ),
            QuestionPriority(
                question='How should the interface be designed?',
                priority=PriorityLevel.MEDIUM,
                score=1.5,
                reasoning='UI keywords detected'
            )
        ]
        
        formatted = processor._format_questions(
            prioritized_questions, 'authentication', None
        )
        
        assert len(formatted) == 2
        assert formatted[0]['question'] == 'What security measures are required?'
        assert formatted[0]['priority'] == 'critical'
        assert formatted[0]['priority_score'] == 3.5
        assert formatted[0]['feature_type'] == 'authentication'
        assert formatted[0]['status'] == 'pending'
        assert 'created_at' in formatted[0]
    
    def test_get_processing_stats(self, processor):
        """Test processing statistics."""
        stats = processor.get_processing_stats()
        
        assert 'cache_size' in stats
        assert 'executor_workers' in stats
        assert 'components' in stats
        assert stats['cache_size'] == 0
        assert stats['executor_workers'] == 2
        assert stats['components']['feature_classifier'] == 'active'
    
    def test_clear_cache(self, processor):
        """Test cache clearing."""
        # Add something to cache
        processor._cache['test_key'] = 'test_value'
        assert len(processor._cache) == 1
        
        processor.clear_cache()
        assert len(processor._cache) == 0


class TestQuestionProcessorIntegration:
    """Test the integrated question processing functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create a question processor instance for testing."""
        return QuestionProcessor(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_process_questions_comprehensive(self, processor):
        """Test comprehensive question processing."""
        questions = [
            'What security measures are required?',
            'How should the interface be designed?',
            'What database should we use?'
        ]
        
        conversation_history = [
            {'type': 'human', 'content': 'I need a secure login system'},
            {'type': 'ai', 'content': 'I understand'},
            {'type': 'human', 'content': 'With high security requirements'}
        ]
        
        answered_questions = [
            {
                'question': 'What authentication method should we use?',
                'status': 'answered',
                'user_answer': 'Email and password'
            }
        ]
        
        pending_questions = [
            {
                'question': 'How should the interface be designed?',
                'status': 'pending',
                'user_answer': None
            }
        ]
        
        # Mock the feature classifier to return a known type
        with patch.object(processor.feature_classifier, 'classify') as mock_classify:
            mock_classify.return_value = Mock(primary_type='authentication')
            
            result = await processor.process_questions(
                questions=questions,
                conversation_history=conversation_history,
                answered_questions=answered_questions,
                pending_questions=pending_questions,
                session_id='test_session'
            )
        
        assert isinstance(result, ProcessedQuestions)
        assert result.feature_type == 'authentication'
        assert result.total_questions > 0
        assert result.processing_time > 0
        assert result.context_insights is not None
        
        # Check that questions are properly formatted
        for question in result.questions:
            assert 'question' in question
            assert 'status' in question
            assert 'priority' in question
            assert 'feature_type' in question
            assert question['feature_type'] == 'authentication'
    
    @pytest.mark.asyncio
    async def test_process_questions_with_caching(self, processor):
        """Test that feature type caching works."""
        conversation_history = [
            {'type': 'human', 'content': 'I need a payment system'}
        ]
        
        # Mock the feature classifier
        with patch.object(processor.feature_classifier, 'classify') as mock_classify:
            mock_classify.return_value = Mock(primary_type='payment')
            
            # First call should hit the classifier
            feature_type1 = await processor._get_feature_type_cached(conversation_history, 'test_session')
            assert feature_type1 == 'payment'
            assert mock_classify.call_count == 1
            
            # Second call should use cache
            feature_type2 = await processor._get_feature_type_cached(conversation_history, 'test_session')
            assert feature_type2 == 'payment'
            assert mock_classify.call_count == 1  # Should not be called again
    
    @pytest.mark.asyncio
    async def test_process_questions_empty_input(self, processor):
        """Test processing with empty input."""
        result = await processor.process_questions(
            questions=[],
            conversation_history=[],
            answered_questions=[],
            pending_questions=[],
            session_id='test_session'
        )
        
        assert isinstance(result, ProcessedQuestions)
        assert result.total_questions == 0
        assert result.prioritized_count == 0
        assert result.contextual_count == 0
    
    @pytest.mark.asyncio
    async def test_process_questions_duplicate_filtering(self, processor):
        """Test that duplicate questions are properly filtered."""
        questions = [
            'What security measures are required?',
            'What security features do we need?',  # Semantic duplicate
            'How should the interface be designed?'
        ]
        
        conversation_history = [
            {'type': 'human', 'content': 'I need a secure login system'}
        ]
        
        answered_questions = [
            {
                'question': 'What security measures are required?',
                'status': 'answered',
                'user_answer': 'Two-factor authentication'
            }
        ]
        
        # Mock the feature classifier
        with patch.object(processor.feature_classifier, 'classify') as mock_classify:
            mock_classify.return_value = Mock(primary_type='authentication')
            
            result = await processor.process_questions(
                questions=questions,
                conversation_history=conversation_history,
                answered_questions=answered_questions,
                pending_questions=[],
                session_id='test_session'
            )
        
        # Should filter out both security questions (one exact, one semantic)
        assert result.total_questions == 1
        assert 'interface' in result.questions[0]['question']


class TestQuestionProcessorPerformance:
    """Test performance aspects of the question processor."""
    
    @pytest.fixture
    def processor(self):
        """Create a question processor instance for testing."""
        return QuestionProcessor(max_workers=4)
    
    @pytest.mark.asyncio
    async def test_processing_time_measurement(self, processor):
        """Test that processing time is properly measured."""
        questions = ['What security measures are required?']
        conversation_history = [{'type': 'human', 'content': 'I need a secure system'}]
        
        # Mock the feature classifier
        with patch.object(processor.feature_classifier, 'classify') as mock_classify:
            mock_classify.return_value = Mock(primary_type='authentication')
            
            result = await processor.process_questions(
                questions=questions,
                conversation_history=conversation_history,
                answered_questions=[],
                pending_questions=[],
                session_id='test_session'
            )
        
        assert result.processing_time > 0
        assert result.processing_time < 10  # Should be fast
    
    def test_concurrent_processing_capacity(self, processor):
        """Test that the processor can handle concurrent requests."""
        assert processor.executor._max_workers == 4
        
        # Test that executor is working
        future = processor.executor.submit(lambda: "test")
        result = future.result()
        assert result == "test"


class TestQuestionProcessorErrorHandling:
    """Test error handling in the question processor."""
    
    @pytest.fixture
    def processor(self):
        """Create a question processor instance for testing."""
        return QuestionProcessor(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_feature_classification_error(self, processor):
        """Test handling of feature classification errors."""
        conversation_history = [{'type': 'human', 'content': 'I need a system'}]
        
        # Mock the feature classifier to raise an exception
        with patch.object(processor.feature_classifier, 'classify') as mock_classify:
            mock_classify.side_effect = Exception("Classification failed")
            
            # Should handle the error gracefully
            with pytest.raises(Exception):
                await processor._get_feature_type_cached(conversation_history, 'test_session')
    
    def test_invalid_question_format(self, processor):
        """Test handling of invalid question formats."""
        # Test with None questions
        filtered = processor._filter_questions(None, [], [])
        assert filtered == []
        
        # Test with empty questions
        filtered = processor._filter_questions([], [], [])
        assert filtered == []
        
        # Test with mixed question types
        questions = ['Valid question', None, '', 'Another valid question']
        filtered = processor._filter_questions(questions, [], [])
        assert len(filtered) == 2
        assert 'Valid question' in filtered
        assert 'Another valid question' in filtered


class TestQuestionProcessorContextIntegration:
    """Test context integration in question processing."""
    
    @pytest.fixture
    def processor(self):
        """Create a question processor instance for testing."""
        return QuestionProcessor(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_context_metadata_in_questions(self, processor):
        """Test that context metadata is included in formatted questions."""
        from src.utils.question_prioritizer import QuestionPriority, PriorityLevel
        from src.utils.context_analyzer import ContextInsight
        
        prioritized_questions = [
            QuestionPriority(
                question='What security measures are required?',
                priority=PriorityLevel.CRITICAL,
                score=3.5,
                reasoning='Security keywords detected'
            )
        ]
        
        context_insight = ContextInsight(
            user_preferences={'security_level': 'high'},
            answered_topics=set(),
            pending_topics=set(),
            conversation_style='technical',
            detail_level='high',
            technical_expertise='expert',
            feature_evolution=[],
            context_gaps=[]
        )
        
        formatted = processor._format_questions(
            prioritized_questions, 'authentication', context_insight
        )
        
        assert len(formatted) == 1
        assert 'context_metadata' in formatted[0]
        assert formatted[0]['context_metadata']['user_expertise'] == 'expert'
        assert formatted[0]['context_metadata']['conversation_style'] == 'technical'
        assert formatted[0]['context_metadata']['detail_level'] == 'high' 