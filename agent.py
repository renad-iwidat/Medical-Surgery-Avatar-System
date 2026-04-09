from openai import OpenAI
import os
from dotenv import load_dotenv
from prompts import get_system_prompt

load_dotenv()

class MedicalAgent:
    """Medical avatar agent using OpenAI"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Remove SSL_CERT_FILE environment variable if it exists to avoid SSL issues
        if 'SSL_CERT_FILE' in os.environ:
            del os.environ['SSL_CERT_FILE']
        
        # Create OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def generate_response(self, scenario: dict, question: str, conversation_history: list) -> str:
        """Generate response from the medical avatar"""
        
        try:
            # Get system prompt from prompts.py (uses the new detailed rules)
            system_prompt = get_system_prompt(scenario, language='ar')
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            for msg in conversation_history:
                role = "user" if msg['role'] == "student" else "assistant"
                messages.append({
                    "role": role,
                    "content": msg['text']
                })
            
            # Add current question
            messages.append({
                "role": "user",
                "content": question
            })
            
            # Call OpenAI with gpt-4o-mini model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "معذرة، حدث خطأ في معالجة سؤالك. حاول مرة أخرى."
