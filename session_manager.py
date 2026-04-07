import uuid
from datetime import datetime
from typing import Dict, Optional
from scenario_manager import ScenarioManager
from prompts import get_system_prompt, get_patient_context

class SessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.sessions = {}
        self.scenario_manager = ScenarioManager()
    
    def create_session(self, student_name: str, department: str, session_type: str) -> Dict:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        # Get scenario
        scenario = self.scenario_manager.get_scenario(session_type)
        if not scenario:
            return {
                'success': False,
                'error': f'السيناريو غير موجود: {session_type}'
            }
        
        # Create session
        self.sessions[session_id] = {
            'id': session_id,
            'student_name': student_name,
            'department': department,
            'session_type': session_type,
            'scenario': scenario,
            'created_at': datetime.now(),
            'messages': [],
            'is_active': True
        }
        
        # Get welcome message
        patient_name = scenario.get('patientInfo', {}).get('name', 'المريض')
        welcome_message = f"مرحباً، أنا {patient_name}. تفضل اسألني يلي بدك ياه."
        
        return {
            'success': True,
            'sessionId': session_id,
            'scenario': scenario,
            'welcomeMessage': welcome_message,
            'duration': 10 * 60 * 1000  # 10 minutes in milliseconds
        }
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, text: str) -> bool:
        """Add message to session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session['messages'].append({
            'role': role,
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
        return True
    
    def end_session(self, session_id: str) -> bool:
        """End a session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session['is_active'] = False
        return True
    
    def get_session_messages(self, session_id: str) -> list:
        """Get all messages from a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session['messages']
