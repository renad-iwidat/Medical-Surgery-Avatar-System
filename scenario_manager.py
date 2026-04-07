import json
import os
from pathlib import Path
from typing import Dict, Optional, List

class ScenarioManager:
    """Manages medical scenarios from JSON files"""
    
    def __init__(self):
        self.scenarios_dir = Path("scenarios")
        self.scenarios = {}
        self.scenarios_list = []
        self.load_scenarios()
    
    def load_scenarios(self):
        """Load all scenarios from JSON files"""
        if not self.scenarios_dir.exists():
            print(f"⚠️  Scenarios directory not found: {self.scenarios_dir}")
            return
        
        # Load morning scenario
        morning_file = self.scenarios_dir / "case-morning.json"
        if morning_file.exists():
            with open(morning_file, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
                scenario['id'] = 'morning'
                scenario['department'] = 'Surgery'
                scenario['session'] = 'morning'
                self.scenarios['morning'] = scenario
                self.scenarios_list.append(scenario)
                print(f"✅ Loaded morning scenario: {scenario.get('title')}")
        else:
            print(f"⚠️  Morning scenario not found: {morning_file}")
        
        # Load evening scenario
        evening_file = self.scenarios_dir / "case-evening.json"
        if evening_file.exists():
            with open(evening_file, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
                scenario['id'] = 'evening'
                scenario['department'] = 'Surgery'
                scenario['session'] = 'evening'
                self.scenarios['evening'] = scenario
                self.scenarios_list.append(scenario)
                print(f"✅ Loaded evening scenario: {scenario.get('title')}")
        else:
            print(f"⚠️  Evening scenario not found: {evening_file}")
    
    def get_all_scenarios(self) -> List[Dict]:
        """Get all scenarios as a list"""
        return self.scenarios_list
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Get scenario by ID (morning/evening)"""
        return self.scenarios.get(scenario_id)
    
    def get_scenario_by_session(self, session_type: str) -> Optional[Dict]:
        """Get scenario by session type (morning/evening) - legacy method"""
        return self.scenarios.get(session_type)
    
    def list_scenarios(self) -> Dict:
        """List all available scenarios"""
        return {
            'morning': self.scenarios.get('morning', {}).get('title', 'Not loaded'),
            'evening': self.scenarios.get('evening', {}).get('title', 'Not loaded')
        }
    
    def get_patient_info(self, session_type: str) -> Optional[Dict]:
        """Get patient info from scenario"""
        scenario = self.get_scenario_by_session(session_type)
        if scenario:
            return scenario.get('patientInfo')
        return None
    
    def get_chief_complaint(self, session_type: str) -> Optional[str]:
        """Get chief complaint from scenario"""
        scenario = self.get_scenario_by_session(session_type)
        if scenario:
            return scenario.get('presentingComplaintFull')
        return None
    
    def get_arabic_translations(self, session_type: str) -> Optional[Dict]:
        """Get Arabic translations from scenario"""
        scenario = self.get_scenario_by_session(session_type)
        if scenario:
            return scenario.get('arabicTranslations', {})
        return None
