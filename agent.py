from openai import OpenAI
import os
from dotenv import load_dotenv

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
            # Get Arabic translations from scenario
            arabic_translations = scenario.get('arabicTranslations', {})
            patient_info_ar = arabic_translations.get('patientInfo', {})
            history_ar = arabic_translations.get('historyOfPresentingComplaint', {})
            
            # Build system prompt with Arabic data from scenario
            patient_name = patient_info_ar.get('name', scenario.get('patientInfo', {}).get('name', 'المريض'))
            patient_age = patient_info_ar.get('age', f"{scenario.get('patientInfo', {}).get('age', 'غير محدد')} سنة")
            chief_complaint = arabic_translations.get('presentingComplaint', {}).get('full', scenario.get('presentingComplaintFull', ''))
            
            # Build detailed context from Arabic translations
            context_parts = [
                f"اسمك: {patient_name}",
                f"عمرك: {patient_age}",
                f"شكواك الرئيسية: {chief_complaint}"
            ]
            
            # Add relevant history from Arabic translations
            if history_ar:
                for key, value in history_ar.items():
                    if isinstance(value, dict) and 'description' in value:
                        context_parts.append(f"- {value.get('description', '')}")
            
            system_prompt = f"""أنت مريض افتراضي في جلسة تدريب طبية OSCE. 

معلوماتك الشخصية:
{chr(10).join(context_parts)}

التعليمات:
1. تحدث باللغة العربية الفصحى والعامية الفلسطينية فقط - لا تستخدم لهجات أخرى
2. كن واقعياً وطبيعياً في الإجابات
3. لا تعطي تشخيصات طبية - أنت مريض وليس طبيب
4. أجب على الأسئلة بناءً على معلومات المريض المعطاة
5. إذا سُئلت عن شيء لا تعرفه، قل "لا أعرف" بطريقة طبيعية
6. حافظ على الشخصية والحالة النفسية للمريض
7. كن متعاوناً مع الطالب
8. استخدم لغة بسيطة وطبيعية وواضحة
9. تجنب المصطلحات الطبية المعقدة
10. أظهر الأعراض والمشاعر المناسبة للحالة
11. كن موجزاً في الإجابات (جملة أو جملتان فقط)
12. استخدم المعلومات من السيناريو فقط"""
            
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
