"""
Feature Type Classifier
Detects common software feature types using pattern matching and keyword analysis.
"""
from typing import Dict, List, Tuple
import re
from dataclasses import dataclass


@dataclass
class FeatureTypeResult:
    """Result of feature type classification."""
    primary_type: str
    confidence: float
    all_types: Dict[str, float]
    keywords_found: List[str]


class FeatureTypeClassifier:
    """
    Classifies software features into common types using pattern matching.
    
    Supported types:
    - authentication: Login, registration, password management, 2FA
    - crud: Create, read, update, delete operations
    - reporting: Dashboards, analytics, data visualization
    - integration: API integrations, third-party services
    - ui: User interface components, forms, navigation
    - api: API endpoints, webhooks, data exchange
    - notification: Email, SMS, push notifications
    - payment: Payment processing, billing, subscriptions
    - search: Search functionality, filtering, sorting
    - workflow: Business processes, approvals, automation
    """
    
    def __init__(self):
        """Initialize the classifier with feature type patterns."""
        self.feature_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, Dict]:
        """Initialize feature type patterns and keywords."""
        return {
            "authentication": {
                "keywords": [
                    "login", "logout", "sign in", "sign out", "register", "registration",
                    "password", "reset password", "forgot password", "two factor", "2fa",
                    "authentication", "authorization", "jwt", "token", "session",
                    "user account", "profile", "credentials", "verify", "verification"
                ],
                "patterns": [
                    r"user.*(login|sign in|authentication)",
                    r"(login|sign in).*system",
                    r"password.*(reset|forgot|recovery)",
                    r"two.?factor.*authentication",
                    r"user.*(register|registration)",
                    r"account.*(create|setup|management)"
                ],
                "weight": 1.0
            },
            "crud": {
                "keywords": [
                    "create", "read", "update", "delete", "add", "remove", "edit",
                    "manage", "list", "view", "show", "display", "store", "save",
                    "insert", "modify", "change", "delete", "remove", "archive"
                ],
                "patterns": [
                    r"(create|add).*(user|item|record|data)",
                    r"(edit|update|modify).*(user|item|record|data)",
                    r"(delete|remove).*(user|item|record|data)",
                    r"(list|view|show).*(user|item|record|data)",
                    r"manage.*(user|item|record|data)"
                ],
                "weight": 0.8
            },
            "reporting": {
                "keywords": [
                    "dashboard", "report", "analytics", "chart", "graph", "statistics",
                    "metrics", "kpi", "data visualization", "insights", "trends",
                    "summary", "overview", "monitoring", "tracking", "performance"
                ],
                "patterns": [
                    r"dashboard.*(view|display|show)",
                    r"report.*(generate|create|view|show)",
                    r"analytics.*(dashboard|report)",
                    r"chart.*(display|show|view)",
                    r"data.*(visualization|insights)",
                    r"reports.*(show|display|user|activity)",
                    r"statistics.*(report|show|display)"
                ],
                "weight": 0.9
            },
            "integration": {
                "keywords": [
                    "api", "integration", "webhook", "third party", "external",
                    "connect", "sync", "import", "export", "webhook", "callback",
                    "oauth", "rest", "graphql", "microservice", "service"
                ],
                "patterns": [
                    r"api.*(integration|connect)",
                    r"third.?party.*(service|integration)",
                    r"webhook.*(receive|send)",
                    r"sync.*(data|information)",
                    r"import.*(data|file)"
                ],
                "weight": 0.85
            },
            "ui": {
                "keywords": [
                    "interface", "form", "button", "modal", "popup", "navigation",
                    "menu", "sidebar", "header", "footer", "layout", "design",
                    "responsive", "mobile", "desktop", "component", "widget"
                ],
                "patterns": [
                    r"user.*interface.*(design|layout)",
                    r"form.*(input|submit|validation)",
                    r"responsive.*(design|layout)",
                    r"mobile.*(app|interface)",
                    r"component.*(ui|interface)"
                ],
                "weight": 0.7
            },
            "notification": {
                "keywords": [
                    "notification", "email", "sms", "push", "alert", "message",
                    "reminder", "announcement", "broadcast", "send", "deliver",
                    "subscribe", "unsubscribe", "preferences", "settings"
                ],
                "patterns": [
                    r"email.*(notification|send|deliver)",
                    r"sms.*(notification|send|deliver)",
                    r"push.*(notification|alert)",
                    r"notification.*(system|service)",
                    r"alert.*(user|send|system)",
                    r"alert.*system.*(administrator|admin)"
                ],
                "weight": 0.8
            },
            "payment": {
                "keywords": [
                    "payment", "billing", "subscription", "invoice", "charge",
                    "credit card", "paypal", "stripe", "transaction", "purchase",
                    "order", "checkout", "cart", "pricing", "plan"
                ],
                "patterns": [
                    r"payment.*(process|gateway|method)",
                    r"billing.*(system|service)",
                    r"subscription.*(manage|billing)",
                    r"credit.?card.*(payment|process)",
                    r"checkout.*(process|payment)",
                    r"invoice.*(generate|management|system)"
                ],
                "weight": 0.9
            },
            "search": {
                "keywords": [
                    "search", "filter", "sort", "query", "find", "lookup",
                    "discover", "browse", "explore", "keyword", "tag",
                    "category", "advanced search", "full text"
                ],
                "patterns": [
                    r"search.*(functionality|feature)",
                    r"filter.*(results|data)",
                    r"advanced.*search",
                    r"full.?text.*search",
                    r"keyword.*(search|find)"
                ],
                "weight": 0.8
            },
            "workflow": {
                "keywords": [
                    "workflow", "process", "approval", "automation", "pipeline",
                    "status", "state", "transition", "step", "stage", "task",
                    "assignment", "delegation", "escalation", "business process"
                ],
                "patterns": [
                    r"workflow.*(process|automation)",
                    r"approval.*(process|workflow)",
                    r"business.*process.*(automation|workflow)",
                    r"status.*(transition|change)",
                    r"task.*(assignment|delegation)"
                ],
                "weight": 0.85
            },
            "general": {
                "keywords": [
                    "simple", "basic", "file", "upload", "download", "calculator",
                    "contact", "form", "system", "feature", "functionality",
                    "tool", "utility", "helper", "assistant", "widget"
                ],
                "patterns": [
                    r"simple.*(system|feature|tool)",
                    r"basic.*(form|system|feature)",
                    r"file.*(upload|download)",
                    r"contact.*form",
                    r"calculator.*(simple|basic)"
                ],
                "weight": 0.5
            }
        }
    
    def classify(self, feature_description: str) -> FeatureTypeResult:
        """
        Classify a feature description into one or more feature types.
        
        Args:
            feature_description (str): The feature description to classify
            
        Returns:
            FeatureTypeResult: Classification result with primary type and confidence
        """
        feature_lower = feature_description.lower()
        type_scores = {}
        keywords_found = []
        
        # Calculate scores for each feature type
        for feature_type, config in self.feature_patterns.items():
            score = 0.0
            type_keywords = []
            
            # Check keyword matches
            for keyword in config["keywords"]:
                if keyword in feature_lower:
                    score += 1.0
                    type_keywords.append(keyword)
            
            # Check pattern matches (weighted higher)
            for pattern in config["patterns"]:
                if re.search(pattern, feature_lower, re.IGNORECASE):
                    score += 3.0  # Increased pattern weight for better specificity
            
            # Apply type weight
            score *= config["weight"]
            
            if score > 0:
                type_scores[feature_type] = score
                keywords_found.extend(type_keywords)
        
        # Find primary type (highest score)
        if type_scores:
            primary_type = max(type_scores, key=type_scores.get)
            max_score = type_scores[primary_type]
            
            # Calculate confidence (improved normalization)
            # Use a more reasonable baseline for confidence calculation
            baseline_score = 5.0  # Reasonable score for a good match
            confidence = min(max_score / baseline_score, 1.0)
            
            # Boost confidence for clear matches
            if max_score >= 3.0:
                confidence = min(confidence * 1.5, 1.0)
        else:
            primary_type = "general"
            confidence = 0.0
        
        # Remove duplicate keywords
        keywords_found = list(set(keywords_found))
        
        return FeatureTypeResult(
            primary_type=primary_type,
            confidence=confidence,
            all_types=type_scores,
            keywords_found=keywords_found
        )
    
    def get_question_templates(self, feature_type: str) -> List[str]:
        """
        Get common question templates for a specific feature type.
        
        Args:
            feature_type (str): The feature type to get templates for
            
        Returns:
            List[str]: List of question templates
        """
        templates = {
            "authentication": [
                "Will users be able to register using their email address or will they need an existing account?",
                "Do you envision any specific password complexity rules (minimum length, special characters, etc.)?",
                "In case of a forgotten password, should the user receive an email with a temporary link for resetting it?",
                "Will there be any additional authentication factors required, like two-factor authentication or biometrics?",
                "Should users be able to stay logged in across browser sessions?",
                "Do you need any specific user roles or permission levels?"
            ],
            "crud": [
                "What type of data will users be able to create, edit, and delete?",
                "Should there be any restrictions on who can perform these operations?",
                "Do you need audit trails to track who made changes and when?",
                "Should deleted items be permanently removed or archived?",
                "Will users need to confirm before deleting important data?",
                "Do you need bulk operations (create/update/delete multiple items at once)?"
            ],
            "reporting": [
                "What specific metrics or data points should be displayed in the dashboard?",
                "Who will have access to view these reports and analytics?",
                "Do you need real-time data updates or is periodic refresh sufficient?",
                "Should users be able to export reports in different formats (PDF, Excel, etc.)?",
                "Do you need customizable dashboards or predefined views?",
                "What time periods should be supported for historical data analysis?"
            ],
            "integration": [
                "Which external services or APIs need to be integrated?",
                "What type of data will be exchanged with these external services?",
                "Do you need real-time synchronization or batch processing?",
                "What should happen if the external service is unavailable?",
                "Do you need webhook support for receiving updates from external services?",
                "Should there be retry logic for failed API calls?"
            ],
            "ui": [
                "What devices and screen sizes should the interface support?",
                "Do you need any specific accessibility features or compliance requirements?",
                "Should the interface be customizable by users or have a fixed design?",
                "Do you need any specific animations or interactive elements?",
                "Should the interface support multiple languages or themes?",
                "What is the expected user flow through the interface?"
            ],
            "notification": [
                "What types of notifications should be sent (email, SMS, push, in-app)?",
                "Who should receive these notifications and when?",
                "Should users be able to customize their notification preferences?",
                "Do you need notification templates or dynamic content?",
                "Should there be any rate limiting or frequency controls?",
                "Do you need delivery confirmation or read receipts?"
            ],
            "payment": [
                "Which payment methods should be supported (credit cards, PayPal, etc.)?",
                "Do you need subscription billing or one-time payments?",
                "What currency and pricing model will be used?",
                "Do you need invoice generation and management?",
                "Should there be any refund or cancellation policies?",
                "Do you need integration with accounting or tax systems?"
            ],
            "search": [
                "What type of content should be searchable?",
                "Do you need advanced search filters or just basic keyword search?",
                "Should search results be ranked by relevance or other criteria?",
                "Do you need search suggestions or autocomplete functionality?",
                "Should search history be saved for users?",
                "Do you need full-text search or just metadata search?"
            ],
            "workflow": [
                "What are the main steps or stages in this workflow?",
                "Who needs to approve or review at each stage?",
                "What should happen if someone is unavailable for approval?",
                "Do you need notifications when workflow status changes?",
                "Should there be time limits or deadlines for each stage?",
                "Do you need the ability to skip or modify workflow steps?"
            ],
            "general": [
                "Who are the primary users of this feature?",
                "What is the main goal or problem this feature solves?",
                "Are there any performance or scalability requirements?",
                "Do you need any specific security or compliance features?",
                "What is the expected timeline for implementing this feature?",
                "Are there any dependencies on other features or systems?"
            ]
        }
        
        return templates.get(feature_type, templates["general"])
    
    def get_feature_type_description(self, feature_type: str) -> str:
        """
        Get a human-readable description of a feature type.
        
        Args:
            feature_type (str): The feature type
            
        Returns:
            str: Description of the feature type
        """
        descriptions = {
            "authentication": "User authentication and authorization features",
            "crud": "Create, read, update, and delete data operations",
            "reporting": "Data visualization, analytics, and reporting features",
            "integration": "Third-party service integrations and API connections",
            "ui": "User interface components and design elements",
            "notification": "Communication and alert systems",
            "payment": "Payment processing and billing features",
            "search": "Search and discovery functionality",
            "workflow": "Business process automation and workflow management",
            "general": "General software features"
        }
        
        return descriptions.get(feature_type, "Unknown feature type") 