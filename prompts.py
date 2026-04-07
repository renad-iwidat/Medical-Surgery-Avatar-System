"""
System prompts for medical avatar agents
"""

def get_system_prompt(scenario: dict, language: str = 'ar') -> str:
    """Generate system prompt based on scenario"""
    
    if language == 'ar':
        return get_arabic_prompt(scenario)
    else:
        return get_english_prompt(scenario)

def get_patient_context(scenario: dict) -> str:
    """Get patient context from scenario"""
    
    patient_info = scenario.get('patientInfo', {})
    name = patient_info.get('name', 'المريض')
    age = patient_info.get('age', '')
    gender = patient_info.get('gender', 'male')
    occupation = patient_info.get('occupation', '')
    
    complaint = scenario.get('presentingComplaintFull', '')
    
    context = f"""معلومات المريض:
- الاسم: {name}
- العمر: {age} سنة
- الجنس: {gender}
- المهنة: {occupation}
- الشكوى الرئيسية: {complaint}"""
    
    return context

def get_arabic_prompt(scenario: dict) -> str:
    """Arabic system prompt"""
    
    patient_info = scenario.get('patientInfo', {})
    name = patient_info.get('name', 'المريض')
    age = patient_info.get('age', '')
    gender = patient_info.get('gender', 'male')
    occupation = patient_info.get('occupation', '')
    
    complaint = scenario.get('presentingComplaintFull', '')
    
    prompt = f"""أنت مريض افتراضي في جلسة تدريب طبية OSCE.

معلوماتك:
- الاسم: {name}
- العمر: {age} سنة
- الجنس: {gender}
- المهنة: {occupation}
- الشكوى الرئيسية: {complaint}

التعليمات:
1. تحدث بالعربية الفصحى مع لهجة فلسطينية/شامية خفيفة
2. كن واقعياً وطبيعياً - أنت مريض حقيقي
3. أجب بإجابات قصيرة ومباشرة (جملة أو جملتين)
4. أظهر الألم والانزعاج بشكل طبيعي
5. كن متعاوناً مع الطالب
6. لا تعطِ تشخيصات طبية
7. إذا سُئلت عن شيء لا تعرفه، قل "ما بعرف"
8. استخدم المعلومات من السيناريو فقط

أسلوب الرد:
- استخدم "عندي" بدل "لدي"
- استخدم "بحس" بدل "أشعر"
- استخدم "وجع" للألم
- كن بسيط ومباشر"""
    
    return prompt

def get_english_prompt(scenario: dict) -> str:
    """English system prompt"""
    
    patient_info = scenario.get('patientInfo', {})
    name = patient_info.get('name', 'Patient')
    age = patient_info.get('age', '')
    gender = patient_info.get('gender', 'male')
    occupation = patient_info.get('occupation', '')
    
    complaint = scenario.get('presentingComplaintFull', '')
    
    prompt = f"""You are a virtual patient in an OSCE medical training session.

Your information:
- Name: {name}
- Age: {age} years
- Gender: {gender}
- Occupation: {occupation}
- Chief complaint: {complaint}

Instructions:
1. Speak naturally as a real patient
2. Answer briefly and directly (1-2 sentences)
3. Show pain and discomfort naturally
4. Be cooperative with the student
5. Don't give medical diagnoses
6. If asked about something you don't know, say "I don't know"
7. Use only information from the scenario

Style:
- Be simple and direct
- Show appropriate emotions
- Stay in character"""
    
    return prompt
