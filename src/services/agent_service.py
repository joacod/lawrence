from typing import Dict, List
import json
import uuid
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings

class AgentService:
    def __init__(self):
        self.llm = ChatOllama(model=settings.MODEL_NAME)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI-powered Product Owner Assistant. Your goal is to clarify software features and generate documentation. When a user describes a feature:
            1. Analyze the feature and, if vague, ask up to 3 specific clarifying questions.
            2. Update a Markdown document with the provided information, including 'Feature', 'Details', and 'Pending Questions' sections.
            3. Maintain conversation context for iterative refinement.
            
            IMPORTANT: You MUST respond with a valid JSON object and ONLY a JSON object. No other text before or after.
            The JSON must follow this exact format with no trailing commas:
            {{
                "response": "Your response text or questions here",
                "markdown": "Your markdown document here"
            }}
            
            The "response" field MUST contain your conversational response to the user, including any clarifying questions.
            The "markdown" field MUST contain the formatted markdown document.
            
            Example of a valid response:
            {{
                "response": "I understand you want to implement user authentication. Could you clarify: 1) What authentication methods do you want to support? 2) Do you need social login integration?",
                "markdown": "# User Authentication\\n\\n## Feature\\nImplement user authentication system\\n\\n## Details\\n- Authentication methods to be determined\\n- Social login integration to be determined\\n\\n## Pending Questions\\n1. What authentication methods do you want to support?\\n2. Do you need social login integration?"
            }}
            
            NEVER leave the "response" field empty. Always provide a conversational response."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        self.chain = self.prompt | self.llm
        self.sessions: Dict[str, List] = {}

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str]:
        session_id = session_id or str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        chat_history = self.sessions[session_id]
        
        result = await self.chain.ainvoke({
            "chat_history": chat_history,
            "input": feature
        })
        
        # Debug print to see raw model response
        print("Raw model response:", result.content)
        
        try:
            # Try to clean the response if it contains any extra text
            content = result.content.strip()
            # Find the first { and last } to extract just the JSON part
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                content = content[start:end]
            
            output = json.loads(content)
            
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            
            self.sessions[session_id] = chat_history
            
            return session_id, output["response"], output["markdown"]
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Failed to parse content: {content}")
            raise ValueError(f"Failed to parse model response as JSON: {str(e)}")

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False 