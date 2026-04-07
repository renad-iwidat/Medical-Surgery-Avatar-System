/**
 * LiveKit Integration
 * Integrates LiveKit with the medical avatar application
 */

console.log('🔵 livekit-integration.js loaded');

let liveKitClient = null;
let currentSession = null;

/**
 * Initialize LiveKit session
 */
async function initializeLiveKitSession(sessionType) {
    console.log(`🎬 Initializing LiveKit session: ${sessionType}`);

    try {
        // Generate unique room name
        const roomName = `medical-avatar-${sessionType}-${Date.now()}`;
        const participantName = document.getElementById('student-name-input')?.value || 'Student';

        console.log(`📍 Room name: ${roomName}`);
        console.log(`👤 Participant: ${participantName}`);

        // Step 1: Create room
        console.log(`📍 Creating room...`);
        const roomResponse = await fetch('/api/livekit/room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                room_name: roomName,
                max_participants: 1
            })
        });

        console.log(`📍 Room response status: ${roomResponse.status}`);

        if (!roomResponse.ok) {
            const errorText = await roomResponse.text();
            console.error(`❌ Room creation failed: ${errorText}`);
            throw new Error(`Failed to create room: ${roomResponse.statusText}`);
        }

        const roomData = await roomResponse.json();
        console.log(`✅ Room created:`, roomData);

        // Step 2: Get token for student
        console.log(`🔑 Generating token for student`);
        const tokenResponse = await fetch('/api/livekit/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                room_name: roomName,
                participant_name: participantName,
                is_agent: false
            })
        });

        console.log(`🔑 Token response status: ${tokenResponse.status}`);

        if (!tokenResponse.ok) {
            const errorText = await tokenResponse.text();
            console.error(`❌ Token generation failed: ${errorText}`);
            throw new Error(`Failed to generate token: ${tokenResponse.statusText}`);
        }

        const tokenData = await tokenResponse.json();
        console.log(`✅ Token generated`);

        // Step 3: Connect to LiveKit
        console.log(`🔗 Connecting to LiveKit...`);
        liveKitClient = new LiveKitClient();
        window.liveKitClient = liveKitClient; // Make it accessible globally
        await liveKitClient.connect(
            roomName,
            participantName,
            tokenData.token,
            tokenData.url
        );

        // Store session info
        currentSession = {
            roomName: roomName,
            sessionType: sessionType,
            participantName: participantName,
            startTime: new Date()
        };

        console.log(`✅ LiveKit session initialized`);
        return true;
    } catch (error) {
        console.error(`❌ Failed to initialize LiveKit session:`, error);
        alert(`خطأ في الاتصال: ${error.message}`);
        return false;
    }
}

// Export immediately
window.initializeLiveKitSession = initializeLiveKitSession;
console.log('✅ initializeLiveKitSession exported to window');

/**
 * Send question to avatar
 */
async function sendQuestionToAvatar(question) {
    if (!liveKitClient || !liveKitClient.isConnected) {
        console.error('❌ Not connected to LiveKit');
        return;
    }

    try {
        // Send message via LiveKit data channel
        await liveKitClient.sendMessage({
            type: 'question',
            text: question,
            timestamp: new Date().toISOString()
        });

        console.log(`✅ Question sent to avatar`);
    } catch (error) {
        console.error(`❌ Failed to send question: ${error}`);
    }
}

/**
 * End LiveKit session
 */
async function endLiveKitSession() {
    try {
        if (liveKitClient) {
            await liveKitClient.disconnect();
            console.log(`✅ LiveKit session ended`);
        }

        // Delete room
        if (currentSession) {
            await fetch(`/api/livekit/room/${currentSession.roomName}`, {
                method: 'DELETE'
            });
            console.log(`✅ Room deleted`);
        }

        liveKitClient = null;
        currentSession = null;
    } catch (error) {
        console.error(`❌ Failed to end session: ${error}`);
    }
}

/**
 * Get LiveKit status
 */
function getLiveKitStatus() {
    if (!liveKitClient) {
        return { connected: false };
    }
    return liveKitClient.getStatus();
}

// Export for use in other scripts
window.initializeLiveKitSession = initializeLiveKitSession;
window.sendQuestionToAvatar = sendQuestionToAvatar;
window.endLiveKitSession = endLiveKitSession;
window.getLiveKitStatus = getLiveKitStatus;
