"""
Student Manager - Handle student data from Excel file
"""

import openpyxl
from pathlib import Path
from typing import List, Dict

class StudentManager:
    """Manage student data from Excel file"""
    
    def __init__(self, excel_path: str = "public/student name.xlsx"):
        self.excel_path = Path(excel_path)
        self.students = []
        self.load_students()
    
    def load_students(self):
        """Load students from Excel file"""
        try:
            # Try different path variations
            paths_to_try = [
                self.excel_path,
                Path("public") / "student name.xlsx",
                Path(".") / "public" / "student name.xlsx",
            ]
            
            excel_file = None
            for path in paths_to_try:
                if Path(path).exists():
                    excel_file = Path(path)
                    break
            
            if not excel_file:
                print(f"⚠️ Excel file not found")
                self.students = []
                return
            
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            # Get all rows
            rows = list(ws.iter_rows(values_only=True))
            
            # Skip first row (title) and process data rows starting from row 1
            for row in rows[1:]:
                # Extract student data
                if row and len(row) >= 3:
                    seq_num = row[0]
                    student_id = row[1]
                    student_name = row[2]
                    
                    # Only process if we have valid data
                    if student_id is None or student_name is None:
                        continue
                    
                    # Skip route entries (they have seq numbers like 372-380 with IDs 99991-99999)
                    # Routes have seq_num >= 372
                    if isinstance(seq_num, int) and seq_num >= 372:
                        continue
                    
                    # Add student
                    if isinstance(student_name, str) and student_name.strip():
                        self.students.append({
                            "id": student_id,
                            "name": student_name.strip(),
                            "seq": seq_num
                        })
            
            print(f"✅ Loaded {len(self.students)} students from Excel")
        
        except Exception as e:
            print(f"❌ Error loading students: {str(e)}")
            import traceback
            traceback.print_exc()
            self.students = []
    
    def get_all_students(self) -> List[Dict]:
        """Get all students"""
        return self.students
    
    def search_students(self, query: str) -> List[Dict]:
        """Search students by name (autocomplete)"""
        if not query or len(query) < 1:
            return []
        
        query_lower = query.lower().strip()
        
        # Search in student names
        results = [
            student for student in self.students
            if query_lower in student['name'].lower()
        ]
        
        # Sort by relevance (starts with query first)
        results.sort(key=lambda x: (
            not x['name'].lower().startswith(query_lower),
            x['name']
        ))
        
        return results[:20]  # Return top 20 results
    
    def get_student_by_name(self, name: str) -> Dict:
        """Get student by exact name"""
        name_lower = name.lower().strip()
        for student in self.students:
            if student['name'].lower() == name_lower:
                return student
        return None
    
    def get_student_by_id(self, student_id: int) -> Dict:
        """Get student by ID"""
        for student in self.students:
            if student['id'] == student_id:
                return student
        return None
