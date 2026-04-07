/**
 * LiveKit Client
 * Handles real-time communication with the medical avatar
 */

class LiveKitClient {
    constructor() {
        this.room = null;
        this.localParticipant = null;
        this.remoteParticipants = new Map();
        this.videoElement = null;
        this.audioElement = null;
        this.isConnected = false;
    }

    /**
     * Initialize LiveKit connection
     */
    async connect(roomName, participantName, token, serverUrl) {
        console.log(`🔗 Connecting to LiveKit room: ${roomName}`);

        try {
            // Check if LiveKit is loaded
            if (typeof LivekitClient === 'undefined') {
                throw new Error('LiveKit SDK not loaded');
            }
            
            // Import LiveKit SDK
            const { Room, RoomEvent, ParticipantEvent } = LivekitClient;

            // Create room
            this.room = new Room({
                audio: true,
                video: {
                    resolution: {
                        width: 640,
                        height: 480
                    }
                }
            });

            // Setup event listeners
            this.setupEventListeners();

            // Connect to room
            await this.room.connect(serverUrl, token);

            this.isConnected = true;
            console.log(`✅ Connected to room: ${roomName}`);

            return true;
        } catch (error) {
            console.error(`❌ Connection failed: ${error}`);
            throw error;
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const { RoomEvent, ParticipantEvent } = LivekitClient;

        console.log('🔧 Setting up event listeners...');

        // Room events
        this.room.on(RoomEvent.ParticipantConnected, (participant) => {
            console.log(`👤 Participant connected: ${participant.name || participant.identity}`);
            this.handleParticipantConnected(participant);
        });

        this.room.on(RoomEvent.ParticipantDisconnected, (participant) => {
            console.log(`👤 Participant disconnected: ${participant.name || participant.identity}`);
            this.remoteParticipants.delete(participant.sid);
        });

        this.room.on(RoomEvent.LocalTrackPublished, (publication, participant) => {
            console.log(`📤 Local track published: ${publication.kind}`);
        });

        this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log(`📥 Track subscribed: ${track.kind} from ${participant.name || participant.identity}`);
            this.handleTrackSubscribed(track, participant);
        });

        this.room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            console.log(`📥 Track unsubscribed: ${track.kind}`);
        });

        this.room.on(RoomEvent.Disconnected, () => {
            console.log(`🔌 Disconnected from room`);
            this.isConnected = false;
        });
        
        // Listen for participant metadata changes (alternative transcription method)
        this.room.on(RoomEvent.ParticipantMetadataChanged, (metadata, participant) => {
            console.log('📊 Participant metadata changed:', participant?.identity);
            console.log('📊 Metadata:', metadata);
            
            try {
                const data = JSON.parse(metadata);
                if (data.last_transcription) {
                    const trans = data.last_transcription;
                    console.log(`📝 Transcription from metadata: ${trans.role} - ${trans.text.substring(0, 50)}...`);
                    
                    if (typeof window.addToTranscript === 'function') {
                        window.addToTranscript(trans.role, trans.text);
                        console.log('✅ Added to transcript from metadata');
                    }
                }
            } catch (error) {
                console.log('⚠️ Could not parse metadata:', error);
            }
        });
        
        // CRITICAL: Listen for data messages (transcriptions)
        // This is the key event for receiving chat messages from the agent
        this.room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
            console.log('📨 ========== DATA RECEIVED ==========');
            console.log('📨 From participant:', participant?.identity || participant?.name || 'unknown');
            console.log('📨 Payload type:', typeof payload);
            console.log('📨 Payload length:', payload?.length || payload?.byteLength);
            
            try {
                // Decode the payload
                let text;
                if (payload instanceof Uint8Array) {
                    const decoder = new TextDecoder();
                    text = decoder.decode(payload);
                } else if (typeof payload === 'string') {
                    text = payload;
                } else {
                    console.error('❌ Unknown payload type:', typeof payload);
                    return;
                }
                
                console.log('📨 Decoded text:', text);
                
                // Parse JSON
                const data = JSON.parse(text);
                console.log('📨 Parsed data:', data);
                
                // Handle transcription messages
                if (data.type === 'transcription') {
                    console.log(`📝 ✅ TRANSCRIPTION: ${data.role} - "${data.text.substring(0, 100)}..."`);
                    
                    // Add to transcript
                    if (typeof window.addToTranscript === 'function') {
                        window.addToTranscript(data.role, data.text);
                        console.log('✅ Successfully added to transcript!');
                    } else {
                        console.error('❌ window.addToTranscript function not found!');
                        console.error('❌ Available window functions:', Object.keys(window).filter(k => k.includes('Transcript')));
                    }
                } else {
                    console.log('⚠️ Unknown data type:', data.type);
                }
            } catch (error) {
                console.error('❌ Failed to parse data message:', error);
                console.error('❌ Error stack:', error.stack);
            }
            
            console.log('📨 ========== END DATA RECEIVED ==========');
        });
        
        console.log('✅ Event listeners setup complete');
    }

    /**
     * Handle participant connected
     */
    handleParticipantConnected(participant) {
        const { ParticipantEvent } = LivekitClient;
        
        console.log(`Adding participant: ${participant.name}`);
        this.remoteParticipants.set(participant.sid, participant);

        // Subscribe to tracks
        participant.on(ParticipantEvent.TrackSubscribed, (track) => {
            this.handleTrackSubscribed(track, participant);
        });
    }

    /**
     * Handle track subscribed
     */
    handleTrackSubscribed(track, participant) {
        console.log(`📹 Track subscribed: ${track.kind} from ${participant.identity}`);

        if (track.kind === 'video') {
            // Display avatar video
            const videoElement = document.getElementById('avatar-video-stream');
            if (videoElement) {
                track.attach(videoElement);
                console.log(`✅ Avatar video displayed`);
            }
        } else if (track.kind === 'audio') {
            // Play avatar audio - handle autoplay policy
            const audioElement = document.getElementById('avatar-audio');
            if (audioElement) {
                // Detach any existing track first
                if (audioElement.srcObject) {
                    const oldTracks = audioElement.srcObject.getTracks();
                    oldTracks.forEach(t => t.stop());
                }
                
                track.attach(audioElement);
                
                // Try to play with user interaction fallback
                audioElement.play().then(() => {
                    console.log(`✅ Avatar audio playing`);
                    
                    // START TIMER when avatar starts speaking
                    if (typeof window.startTimer === 'function') {
                        window.startTimer();
                        console.log('⏱️ Timer started when avatar audio began');
                    }
                }).catch(err => {
                    console.warn('⚠️ Audio autoplay blocked, showing enable button');
                    
                    // Show audio enable overlay
                    const overlay = document.getElementById('audio-enable-overlay');
                    if (overlay) {
                        overlay.classList.remove('hidden');
                    }
                });
            }
        }
    }

    /**
     * Publish local audio
     */
    async publishAudio(stream) {
        try {
            if (!this.room || !this.isConnected) {
                throw new Error('Not connected to room');
            }
            
            const audioTrack = stream.getAudioTracks()[0];
            if (!audioTrack) {
                throw new Error('No audio track found');
            }
            
            // Create LocalAudioTrack
            const { LocalAudioTrack } = LivekitClient;
            const localTrack = new LocalAudioTrack(audioTrack);
            
            // Publish track
            await this.room.localParticipant.publishTrack(localTrack, {
                name: 'microphone',
                source: 'microphone'
            });
            
            console.log(`✅ Audio track published to LiveKit`);
            
            // Listen for transcription on this track
            this.setupTranscriptionListener();
            
            return localTrack;
        } catch (error) {
            console.error(`❌ Failed to publish audio: ${error}`);
            throw error;
        }
    }
    
    /**
     * Setup transcription listener - Alternative method
     */
    setupTranscriptionListener() {
        console.log('🎤 Setting up transcription listener...');
        
        // Listen for agent's transcription events
        if (this.room && this.room.remoteParticipants) {
            this.room.remoteParticipants.forEach(participant => {
                console.log('👤 Checking participant:', participant.identity);
                
                // Listen for transcription from agent
                participant.on('transcriptionReceived', (transcription) => {
                    console.log('📝 Transcription received:', transcription);
                    if (window.addToTranscript) {
                        window.addToTranscript('avatar', transcription.text);
                    }
                });
            });
        }
    }

    /**
     * Send data message
     */
    async sendMessage(message) {
        try {
            const encoder = new TextEncoder();
            const data = encoder.encode(JSON.stringify(message));
            await this.room.localParticipant.publishData(data, {
                reliable: true
            });
            console.log(`✅ Message sent`);
        } catch (error) {
            console.error(`❌ Failed to send message: ${error}`);
        }
    }

    /**
     * Disconnect from room
     */
    async disconnect() {
        try {
            if (this.room) {
                await this.room.disconnect();
                this.isConnected = false;
                console.log(`✅ Disconnected from room`);
            }
        } catch (error) {
            console.error(`❌ Disconnect failed: ${error}`);
        }
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            room: this.room?.name,
            participants: this.remoteParticipants.size
        };
    }
}

// Export for use in other scripts
window.LiveKitClient = LiveKitClient;
