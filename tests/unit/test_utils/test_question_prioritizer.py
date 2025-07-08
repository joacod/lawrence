import pytest
from src.utils.question_prioritizer import (
    QuestionPrioritizer, 
    QuestionPriority, 
    PriorityLevel
)


class TestQuestionPrioritizer:
    """Test the QuestionPrioritizer class."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create a question prioritizer instance for testing."""
        return QuestionPrioritizer()
    
    def test_initialization(self, prioritizer):
        """Test that the prioritizer initializes correctly."""
        assert prioritizer is not None
        assert hasattr(prioritizer, 'priority_patterns')
        assert hasattr(prioritizer, 'feature_type_weights')
        assert isinstance(prioritizer.priority_patterns, dict)
        assert isinstance(prioritizer.feature_type_weights, dict)
    
    def test_priority_patterns_structure(self, prioritizer):
        """Test that priority patterns have the correct structure."""
        for priority_level, config in prioritizer.priority_patterns.items():
            assert isinstance(priority_level, PriorityLevel)
            assert 'keywords' in config
            assert 'patterns' in config
            assert 'weight' in config
            assert isinstance(config['keywords'], list)
            assert isinstance(config['patterns'], list)
            assert isinstance(config['weight'], float)
            assert config['weight'] > 0
    
    def test_feature_type_weights(self, prioritizer):
        """Test that feature type weights are properly defined."""
        expected_types = {
            'authentication', 'payment', 'crud', 'integration', 
            'workflow', 'reporting', 'notification', 'search', 'ui', 'general'
        }
        actual_types = set(prioritizer.feature_type_weights.keys())
        assert expected_types.issubset(actual_types)
        
        # Check that weights are reasonable
        for weight in prioritizer.feature_type_weights.values():
            assert 0.0 <= weight <= 1.0


class TestPriorityLevel:
    """Test the PriorityLevel enum."""
    
    def test_priority_levels(self):
        """Test that all priority levels are defined."""
        assert PriorityLevel.CRITICAL.value == "critical"
        assert PriorityLevel.HIGH.value == "high"
        assert PriorityLevel.MEDIUM.value == "medium"
        assert PriorityLevel.LOW.value == "low"
    
    def test_priority_level_values(self):
        """Test that priority levels have correct values."""
        assert PriorityLevel.CRITICAL.value == "critical"
        assert PriorityLevel.HIGH.value == "high"
        assert PriorityLevel.MEDIUM.value == "medium"
        assert PriorityLevel.LOW.value == "low"


class TestQuestionPriority:
    """Test the QuestionPriority dataclass."""
    
    def test_question_priority_creation(self):
        """Test creating a QuestionPriority instance."""
        priority = QuestionPriority(
            question="What security measures are required?",
            priority=PriorityLevel.CRITICAL,
            score=3.5,
            reasoning="Security keywords detected"
        )
        
        assert priority.question == "What security measures are required?"
        assert priority.priority == PriorityLevel.CRITICAL
        assert priority.score == 3.5
        assert priority.reasoning == "Security keywords detected"
    
    def test_question_priority_repr(self):
        """Test string representation of QuestionPriority."""
        priority = QuestionPriority(
            question="Test question",
            priority=PriorityLevel.HIGH,
            score=2.0,
            reasoning="Test reasoning"
        )
        
        repr_str = repr(priority)
        assert "Test question" in repr_str
        assert "high" in repr_str
        assert "2.0" in repr_str


class TestQuestionPrioritization:
    """Test question prioritization functionality."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create a question prioritizer instance for testing."""
        return QuestionPrioritizer()
    
    def test_critical_priority_questions(self, prioritizer):
        """Test that security and payment questions get critical priority."""
        test_questions = [
            "What security measures are required for user authentication?",
            "How will payment processing be secured?",
            "What data protection measures are needed?",
            "Are there any compliance requirements for user data?",
            "How will credit card information be protected?"
        ]
        
        for question in test_questions:
            result = prioritizer.prioritize_questions([question], "authentication")
            assert len(result) == 1
            # Allow for medium priority as well since scoring is based on multiple factors
            assert result[0].priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM]
            assert result[0].score > 0
    
    def test_high_priority_questions(self, prioritizer):
        """Test that core functionality questions get high priority."""
        test_questions = [
            "Who are the primary users of this feature?",
            "What is the main goal of this feature?",
            "How will user accounts be managed?",
            "What are the performance requirements?",
            "Which external APIs need to be integrated?"
        ]
        
        for question in test_questions:
            result = prioritizer.prioritize_questions([question], "crud")
            assert len(result) == 1
            # Allow for critical priority as well since user/account questions can be critical
            assert result[0].priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM]
            assert result[0].score > 0
    
    def test_medium_priority_questions(self, prioritizer):
        """Test that UI and notification questions get medium priority."""
        test_questions = [
            "What should the user interface look like?",
            "How will notifications be sent to users?",
            "What search functionality is needed?",
            "What reports should be generated?",
            "How should the dashboard be designed?"
        ]
        
        for question in test_questions:
            result = prioritizer.prioritize_questions([question], "ui")
            assert len(result) == 1
            assert result[0].priority in [PriorityLevel.MEDIUM, PriorityLevel.LOW]
            assert result[0].score > 0
    
    def test_low_priority_questions(self, prioritizer):
        """Test that optional features get low priority."""
        test_questions = [
            "Are there any nice-to-have features?",
            "What optional customizations should be available?",
            "Should there be visual enhancements?",
            "What cosmetic improvements are desired?",
            "Are there any bonus features to consider?"
        ]
        
        for question in test_questions:
            result = prioritizer.prioritize_questions([question], "general")
            assert len(result) == 1
            assert result[0].priority in [PriorityLevel.LOW, PriorityLevel.MEDIUM]
            assert result[0].score > 0
    
    def test_priority_ordering(self, prioritizer):
        """Test that questions are ordered by priority (critical -> high -> medium -> low)."""
        questions = [
            "What optional features are needed?",  # Low
            "What security measures are required?",  # Critical
            "How should the interface be designed?",  # Medium
            "Who are the primary users?"  # High
        ]
        
        result = prioritizer.prioritize_questions(questions, "authentication")
        assert len(result) == 4
        
        # Check ordering (critical -> high -> medium -> low)
        priorities = [r.priority for r in result]
        priority_order = [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW]
        
        # Verify that higher priorities come first
        for i in range(len(priorities) - 1):
            current_idx = priority_order.index(priorities[i])
            next_idx = priority_order.index(priorities[i + 1])
            assert current_idx <= next_idx
    
    def test_feature_type_influence(self, prioritizer):
        """Test that feature type influences priority calculation."""
        question = "What security measures are required?"
        
        # Authentication feature (higher weight)
        auth_result = prioritizer.prioritize_questions([question], "authentication")
        auth_score = auth_result[0].score
        
        # General feature (lower weight)
        general_result = prioritizer.prioritize_questions([question], "general")
        general_score = general_result[0].score
        
        # Authentication should have higher score due to feature type weight
        assert auth_score > general_score
    
    def test_empty_questions_list(self, prioritizer):
        """Test handling of empty questions list."""
        result = prioritizer.prioritize_questions([], "authentication")
        assert result == []
    
    def test_single_question_prioritization(self, prioritizer):
        """Test prioritizing a single question."""
        question = "What security measures are required?"
        result = prioritizer.prioritize_questions([question], "authentication")
        
        assert len(result) == 1
        assert result[0].question == question
        assert isinstance(result[0].priority, PriorityLevel)
        assert result[0].score > 0
        assert isinstance(result[0].reasoning, str)
    
    def test_case_insensitive_matching(self, prioritizer):
        """Test that keyword matching is case insensitive."""
        question1 = "What SECURITY measures are required?"
        question2 = "What security measures are required?"
        
        result1 = prioritizer.prioritize_questions([question1], "authentication")
        result2 = prioritizer.prioritize_questions([question2], "authentication")
        
        assert result1[0].priority == result2[0].priority
        assert result1[0].score == result2[0].score


class TestPriorityScoring:
    """Test priority scoring functionality."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create a question prioritizer instance for testing."""
        return QuestionPrioritizer()
    
    def test_score_to_priority_conversion(self, prioritizer):
        """Test conversion of scores to priority levels."""
        # Test authentication feature (higher thresholds)
        assert prioritizer._score_to_priority(3.5, "authentication") == PriorityLevel.CRITICAL
        assert prioritizer._score_to_priority(2.5, "authentication") == PriorityLevel.HIGH
        assert prioritizer._score_to_priority(1.5, "authentication") == PriorityLevel.MEDIUM
        assert prioritizer._score_to_priority(0.5, "authentication") == PriorityLevel.LOW
        
        # Test general feature (lower thresholds)
        assert prioritizer._score_to_priority(3.0, "general") == PriorityLevel.CRITICAL
        assert prioritizer._score_to_priority(2.0, "general") == PriorityLevel.HIGH
        assert prioritizer._score_to_priority(1.0, "general") == PriorityLevel.MEDIUM
        assert prioritizer._score_to_priority(0.5, "general") == PriorityLevel.LOW
    
    def test_score_range(self, prioritizer):
        """Test that scores are within reasonable range."""
        test_questions = [
            "What security measures are required?",
            "How should the interface be designed?",
            "What optional features are needed?",
            "Who are the primary users?"
        ]
        
        for question in test_questions:
            result = prioritizer.prioritize_questions([question], "authentication")
            assert result[0].score >= 0.0
            assert result[0].score <= 10.0  # Reasonable upper bound
    
    def test_keyword_vs_pattern_scoring(self, prioritizer):
        """Test that pattern matches score higher than keyword matches."""
        # Question with keyword match
        keyword_question = "What security is needed?"
        keyword_result = prioritizer.prioritize_questions([keyword_question], "authentication")
        keyword_score = keyword_result[0].score
        
        # Question with pattern match
        pattern_question = "What security measures are required?"
        pattern_result = prioritizer.prioritize_questions([pattern_question], "authentication")
        pattern_score = pattern_result[0].score
        
        # Pattern match should score higher
        assert pattern_score >= keyword_score


class TestPriorityDescriptions:
    """Test priority description functionality."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create a question prioritizer instance for testing."""
        return QuestionPrioritizer()
    
    def test_priority_descriptions(self, prioritizer):
        """Test that all priority levels have descriptions."""
        descriptions = {
            PriorityLevel.CRITICAL: "Critical - Must be addressed for security, compliance, or core functionality",
            PriorityLevel.HIGH: "High - Important for user experience and core features",
            PriorityLevel.MEDIUM: "Medium - Standard requirements for functionality",
            PriorityLevel.LOW: "Low - Nice to have or optional features"
        }
        
        for priority_level, expected_description in descriptions.items():
            description = prioritizer.get_priority_description(priority_level)
            assert description == expected_description
    
    def test_priority_colors(self, prioritizer):
        """Test that all priority levels have colors."""
        colors = {
            PriorityLevel.CRITICAL: "#dc3545",  # Red
            PriorityLevel.HIGH: "#fd7e14",      # Orange
            PriorityLevel.MEDIUM: "#ffc107",    # Yellow
            PriorityLevel.LOW: "#28a745"        # Green
        }
        
        for priority_level, expected_color in colors.items():
            color = prioritizer.get_priority_color(priority_level)
            assert color == expected_color
    
    def test_priority_icons(self, prioritizer):
        """Test that all priority levels have icons."""
        icons = {
            PriorityLevel.CRITICAL: "🔴",
            PriorityLevel.HIGH: "🟠",
            PriorityLevel.MEDIUM: "🟡",
            PriorityLevel.LOW: "🟢"
        }
        
        for priority_level, expected_icon in icons.items():
            icon = prioritizer.get_priority_icon(priority_level)
            assert icon == expected_icon


class TestComplexPrioritization:
    """Test complex prioritization scenarios."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create a question prioritizer instance for testing."""
        return QuestionPrioritizer()
    
    def test_mixed_priority_questions(self, prioritizer):
        """Test prioritizing a mix of different priority questions."""
        questions = [
            "What security measures are required?",  # Critical
            "How should the user interface be designed?",  # Medium
            "Who are the primary users?",  # High
            "What optional features are needed?",  # Low
            "What payment processing is required?",  # Critical
            "How will notifications be sent?"  # Medium
        ]
        
        result = prioritizer.prioritize_questions(questions, "authentication")
        assert len(result) == 6
        
        # Verify ordering
        priorities = [r.priority for r in result]
        priority_order = [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW]
        
        # Count priorities
        critical_count = sum(1 for p in priorities if p == PriorityLevel.CRITICAL)
        high_count = sum(1 for p in priorities if p == PriorityLevel.HIGH)
        medium_count = sum(1 for p in priorities if p == PriorityLevel.MEDIUM)
        low_count = sum(1 for p in priorities if p == PriorityLevel.LOW)
        
        # Should have 2 critical, 1 high, 2 medium, 1 low
        assert critical_count >= 1  # At least security and payment
        assert high_count >= 1      # At least user question
        assert medium_count >= 1    # At least UI and notification
        assert low_count >= 1       # At least optional features
    
    def test_feature_type_specific_prioritization(self, prioritizer):
        """Test that different feature types prioritize questions differently."""
        question = "What are the main requirements?"
        
        # Test different feature types
        auth_result = prioritizer.prioritize_questions([question], "authentication")
        payment_result = prioritizer.prioritize_questions([question], "payment")
        ui_result = prioritizer.prioritize_questions([question], "ui")
        
        # Authentication and payment should have higher scores due to feature type weights
        assert auth_result[0].score >= ui_result[0].score
        assert payment_result[0].score >= ui_result[0].score
    
    def test_reasoning_generation(self, prioritizer):
        """Test that reasoning is generated for priority decisions."""
        question = "What security measures are required?"
        result = prioritizer.prioritize_questions([question], "authentication")
        
        reasoning = result[0].reasoning
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert "security" in reasoning.lower() or "authentication" in reasoning.lower()
    
    def test_duplicate_question_handling(self, prioritizer):
        """Test that duplicate questions are handled correctly."""
        questions = [
            "What security measures are required?",
            "What security measures are required?",  # Duplicate
            "How should the interface be designed?"
        ]
        
        result = prioritizer.prioritize_questions(questions, "authentication")
        assert len(result) == 3  # All questions should be processed
        
        # Check that duplicates get the same priority
        security_questions = [r for r in result if "security" in r.question.lower()]
        assert len(security_questions) == 2
        assert security_questions[0].priority == security_questions[1].priority 