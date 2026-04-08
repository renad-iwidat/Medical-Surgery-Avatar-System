/**
 * Medical Avatar App - LiveKit Version
 * Updated to use LiveKit for real-time communication
 */

// Global variables
let currentSessionType = null;
let currentStudentName = null;
let sessionStartTime = null;
let sessionDuration = 600; // 10 minutes in seconds
let timerInterval = null;

// ===== SCREEN NAVIGATION =====

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

function goBack(screenId) {
    showScreen(screenId);
}

// ===== PASSWORD SCREEN =====

function checkPassword() {
    const password = document.getElementById('password-input').value;
    const correctPassword = 'surgery2024';
    
    if (password === correctPassword) {
        document.getElementById('password-error').textContent = '';
        showScreen('welcome-screen');
    } else {
        document.getElementById('password-error').textContent = '❌ كلمة المرور غير صحيحة';
    }
}

// ===== WELCOME SCREEN =====

function selectDepartment(dept) {
    showScreen('session-selection-screen');
}

// ===== SESSION SELECTION =====

function selectSession(session) {
    currentSessionType = session;
    showScreen('student-name-screen');
}

// ===== STUDENT NAME SCREEN =====

function confirmStudentName() {
    console.log('🔵 confirmStudentName called');
    const nameInput = document.getElementById('student-name-input');
    const name = nameInput.value.trim();
    
    console.log('📝 Student name:', name);
    
    if (!name) {
        alert('الرجاء إدخال اسمك');
        return;
    }
    
    currentStudentName = name;
    console.log('✅ Starting session with name:', currentStudentName);
    console.log('✅ Session type:', currentSessionType);
    startSession();
}

// ===== SESSION MANAGEMENT =====

async function startSession() {
    console.log(`🎬 Starting session: ${currentSessionType}`);
    console.log(`👤 Student name: ${currentStudentName}`);
    
    try {
        console.log('🔄 Calling initializeLiveKitSession...');
        
        // Check if function exists
        if (typeof initializeLiveKitSession === 'undefined') {
            console.error('❌ initializeLiveKitSession is not defined!');
            alert('خطأ: لم يتم تحميل LiveKit بشكل صحيح');
            return;
        }
        
        // Initialize LiveKit session
        const success = await initializeLiveKitSession(currentSessionType);
        
        console.log('✅ initializeLiveKitSession returned:', success);
        
        if (!success) {
            alert('فشل الاتصال بالخادم');
            return;
        }
        
        // Show session screen
        showScreen('session-screen');
        document.getElementById('main-header').style.display = 'block';
        
        // Load scenario
        const scenario = await loadScenario(currentSessionType);
        
        // DON'T start timer here - it will start when avatar audio plays
        sessionStartTime = Date.now();
        console.log('⏱️ Session start time recorded, but timer will start when avatar speaks');
        
        // Show greeting immediately in transcript
        if (scenario) {
            const patientName = scenario.arabicTranslations?.patientInfo?.name || 'المريض';
            // Remove "السيد" or "السيدة" prefix
            const cleanName = patientName.replace('السيد ', '').replace('السيدة ', '');
            // NEW GREETING - exactly as requested
            const greeting = `مرحباً، أنا ${cleanName}. دكتور، مش حاس حالي منيح اليوم. شو ممكن يكون السبب برأيك؟`;
            
            // Add greeting ONCE after a delay to avoid duplication
            setTimeout(() => {
                const transcript = document.getElementById('transcript');
                // Check if greeting already exists
                if (!transcript.textContent.includes(greeting)) {
                    addToTranscript('avatar', greeting);
                    console.log('👋 Patient greeting displayed');
                }
            }, 2000);
        }
        
        console.log(`✅ Session started`);
    } catch (error) {
        console.error(`❌ Failed to start session:`, error);
        alert(`خطأ: ${error.message}`);
    }
}

// ===== TIMER =====

let timerStarted = false; // Flag to ensure timer starts only once

function startTimer() {
    // Prevent starting timer multiple times
    if (timerStarted) {
        console.log('⏱️ Timer already started, skipping');
        return;
    }
    
    timerStarted = true;
    let elapsedSeconds = 0;
    
    timerInterval = setInterval(() => {
        elapsedSeconds++;
        
        const minutes = Math.floor(elapsedSeconds / 60);
        const seconds = elapsedSeconds % 60;
        const timeString = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        document.getElementById('session-timer').textContent = timeString;
        
        // Check if time is up
        if (elapsedSeconds >= sessionDuration) {
            stopTimer();
            endSession();
        }
    }, 1000);
    
    console.log('⏱️ Timer started!');
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
        timerStarted = false;
    }
}

// Make startTimer available globally
window.startTimer = startTimer;

// ===== SCENARIO LOADING =====

async function loadScenario(sessionType) {
    try {
        const scenarioId = sessionType === 'morning' ? 'morning' : 'evening';
        const response = await fetch(`/api/scenarios/${scenarioId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load scenario');
        }
        
        const scenario = await response.json();
        
        // Display patient info (without duplication)
        displayPatientInfo(scenario);
        
        console.log(`✅ Scenario loaded: ${scenario.title}`);
        
        return scenario;
    } catch (error) {
        console.error(`❌ Failed to load scenario: ${error}`);
        return null;
    }
}

function displayPatientInfo(scenario) {
    const patientInfo = scenario.arabicTranslations?.patientInfo || {};
    const name = patientInfo.name || 'المريض';
    const age = patientInfo.age || '';
    const gender = patientInfo.gender || '';
    const occupation = patientInfo.occupation || '';
    
    document.getElementById('patient-info').innerHTML = `
        <p><strong>الاسم:</strong> ${name}</p>
        <p><strong>العمر:</strong> ${age}</p>
        <p><strong>الجنس:</strong> ${gender}</p>
        <p><strong>المهنة:</strong> ${occupation}</p>
    `;
    
    // Display chief complaint
    const complaint = scenario.arabicTranslations?.presentingComplaint?.full || '';
    document.getElementById('chief-complaint').innerHTML = `
        <p>${complaint}</p>
    `;
}

// ===== MESSAGE HANDLING =====

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add to transcript
    addToTranscript('student', message);
    input.value = '';
    
    try {
        // Send to avatar via LiveKit
        await sendQuestionToAvatar(message);
        
        // Get response from backend
        const response = await fetch('/api/session/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: 'livekit-session',
                message: message
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const avatarResponse = data.response;
            
            // Add avatar response to transcript
            addToTranscript('avatar', avatarResponse);
            
            // Generate speech
            await speak(avatarResponse);
        }
    } catch (error) {
        console.error(`❌ Failed to send message: ${error}`);
    }
}

function addToTranscript(role, message) {
    const transcript = document.getElementById('transcript');
    if (!transcript) {
        console.error('❌ Transcript element not found');
        return;
    }
    
    console.log(`📝 Adding to transcript: ${role} - ${message.substring(0, 50)}...`);
    
    // Remove placeholder if exists
    const placeholder = transcript.querySelector('.transcript-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const item = document.createElement('div');
    item.className = `transcript-item ${role}`;
    
    const roleLabel = role === 'student' ? 'أنت' : 'المريض';
    
    item.innerHTML = `
        <strong>${roleLabel}:</strong> ${message}
    `;
    
    transcript.appendChild(item);
    
    // Auto-scroll to bottom
    transcript.scrollTop = transcript.scrollHeight;
    
    console.log('✅ Added to transcript successfully');
}

// Make it accessible globally
window.addToTranscript = addToTranscript;

// Poll for agent responses (simple solution)
let lastAgentResponse = '';
let pollInterval = null;

async function pollAgentResponses() {
    // This is a fallback - we'll capture from audio
    // For now, just log
    console.log('📊 Polling for agent responses...');
}

// Start polling when session starts
function startResponsePolling() {
    if (pollInterval) return;
    
    pollInterval = setInterval(pollAgentResponses, 1000);
    console.log('✅ Started response polling');
}

function stopResponsePolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
        console.log('⏹️ Stopped response polling');
    }
}

// ===== SPEECH =====

async function speak(text) {
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                gender: 'male'
            })
        });
        
        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play().catch(err => console.error('Audio play error:', err));
        }
    } catch (error) {
        console.error(`❌ TTS error: ${error}`);
    }
}

// ===== SESSION END =====

async function endSession() {
    console.log(`🔚 Ending session`);
    
    stopTimer();
    
    try {
        // End LiveKit session
        await endLiveKitSession();
        
        // Reset
        currentSessionType = null;
        currentStudentName = null;
        
        // Go back to student name screen
        showScreen('student-name-screen');
        document.getElementById('main-header').style.display = 'block';
        
        // Clear the input field
        document.getElementById('student-name-input').value = '';
        
        console.log(`✅ Session ended - returning to student name screen`);
    } catch (error) {
        console.error(`❌ Failed to end session: ${error}`);
    }
}

// ===== NEW SESSION =====

document.getElementById('new-session-btn')?.addEventListener('click', () => {
    endLiveKitSession();
    showScreen('password-screen');
    document.getElementById('password-input').value = '';
});

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ App initialized');
    
    // Add mic button click handler
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.addEventListener('click', toggleMicrophone);
        console.log('✅ Mic button handler attached');
    }
    
    // Add send button handler
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Add enter key handler for message input
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});

// ===== MICROPHONE CONTROL =====

let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];

async function toggleMicrophone() {
    console.log('🎤 Microphone toggle');
    
    const micBtn = document.getElementById('mic-btn');
    const micStatus = document.getElementById('mic-status');
    const videoSection = document.querySelector('.video-section');
    const recordingOverlay = document.getElementById('recording-overlay');
    
    if (!isRecording) {
        // Start recording
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // Setup speech recognition for transcription
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'ar-SA';
                recognition.continuous = false;
                recognition.interimResults = false;
                
                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    console.log('🎤 Student said:', transcript);
                    
                    // Add to transcript immediately
                    addToTranscript('student', transcript);
                };
                
                recognition.onerror = (event) => {
                    console.error('Speech recognition error:', event.error);
                };
                
                recognition.start();
                window.currentRecognition = recognition;
            }
            
            // Publish audio to LiveKit
            if (window.liveKitClient && window.liveKitClient.isConnected) {
                await window.liveKitClient.publishAudio(stream);
                
                isRecording = true;
                micBtn.classList.add('recording');
                micStatus.classList.add('recording');
                videoSection.classList.add('recording');
                recordingOverlay.classList.remove('hidden');
                micStatus.textContent = '🔴 جاهز... تكلم الآن!';
                
                console.log('✅ Microphone started and publishing to LiveKit');
            } else {
                console.error('❌ LiveKit not connected');
                alert('خطأ: لم يتم الاتصال بـ LiveKit');
                stream.getTracks().forEach(track => track.stop());
            }
        } catch (error) {
            console.error('❌ Microphone error:', error);
            alert('فشل تفعيل الميكروفون. الرجاء السماح بالوصول للميكروفون.');
        }
    } else {
        // Stop recording
        if (window.currentRecognition) {
            window.currentRecognition.stop();
            window.currentRecognition = null;
        }
        
        if (window.liveKitClient && window.liveKitClient.room) {
            // Unpublish audio tracks
            const localParticipant = window.liveKitClient.room.localParticipant;
            if (localParticipant) {
                localParticipant.audioTracks.forEach((publication) => {
                    localParticipant.unpublishTrack(publication.track);
                });
            }
        }
        
        isRecording = false;
        micBtn.classList.remove('recording');
        micStatus.classList.remove('recording');
        videoSection.classList.remove('recording');
        recordingOverlay.classList.add('hidden');
        micStatus.textContent = '🎤 اضغط مطولاً على مسطرة الكيبورد (Space) للتحدث، ثم ارفع إصبعك لإرسال السؤال';
        
        console.log('✅ Microphone stopped');
    }
}

// Keyboard shortcut for microphone (Space key) - Push to talk
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !e.repeat) {
        // Don't trigger if typing in input field
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') return;
        // Only work during session
        if (!currentSessionType) return;
        e.preventDefault();
        if (!isRecording) {
            toggleMicrophone();
        }
    }
});

document.addEventListener('keyup', (e) => {
    if (e.code === 'Space') {
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') return;
        if (!currentSessionType) return;
        e.preventDefault();
        if (isRecording) {
            toggleMicrophone();
        }
    }
});

// Make functions global
window.checkPassword = checkPassword;
window.selectDepartment = selectDepartment;
window.selectSession = selectSession;
window.confirmStudentName = confirmStudentName;
window.goBack = goBack;
window.sendMessage = sendMessage;
window.endSession = endSession;
window.toggleMicrophone = toggleMicrophone;

// Enable audio function
window.enableAudio = function() {
    const audioElement = document.getElementById('avatar-audio');
    const overlay = document.getElementById('audio-enable-overlay');
    
    if (audioElement) {
        audioElement.play().then(() => {
            console.log('✅ Audio enabled by user');
            if (overlay) {
                overlay.classList.add('hidden');
            }
        }).catch(err => {
            console.error('❌ Failed to enable audio:', err);
        });
    }
};
