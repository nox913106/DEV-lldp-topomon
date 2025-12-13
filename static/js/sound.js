/**
 * Alert Sound Player
 * Plays notification sounds for critical alerts
 */

const AlertSound = {
    audioContext: null,

    // Initialize audio context
    init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
    },

    // Check if sound alerts are enabled
    isEnabled() {
        return localStorage.getItem('notify_sound') === 'true';
    },

    // Enable/disable sound alerts
    setEnabled(enabled) {
        localStorage.setItem('notify_sound', enabled ? 'true' : 'false');
    },

    // Play a beep sound
    playBeep(frequency = 800, duration = 200, type = 'sine') {
        if (!this.isEnabled()) return;

        try {
            this.init();

            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);

            oscillator.frequency.value = frequency;
            oscillator.type = type;

            gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);

            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + duration / 1000);
        } catch (e) {
            console.warn('Unable to play sound:', e);
        }
    },

    // Play warning sound (two beeps)
    playWarning() {
        this.playBeep(600, 150);
        setTimeout(() => this.playBeep(600, 150), 200);
    },

    // Play critical alert sound (urgent pattern)
    playCritical() {
        this.playBeep(800, 100);
        setTimeout(() => this.playBeep(1000, 100), 150);
        setTimeout(() => this.playBeep(800, 100), 300);
        setTimeout(() => this.playBeep(1000, 100), 450);
    },

    // Play success sound
    playSuccess() {
        this.playBeep(523, 100);  // C5
        setTimeout(() => this.playBeep(659, 100), 100);  // E5
        setTimeout(() => this.playBeep(784, 150), 200);  // G5
    },

    // Test sound (for settings page)
    playTest() {
        const wasEnabled = this.isEnabled();
        this.setEnabled(true);
        this.playCritical();
        if (!wasEnabled) {
            setTimeout(() => this.setEnabled(false), 1000);
        }
    }
};

// Export for use
window.AlertSound = AlertSound;
