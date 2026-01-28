/**
 * CODEX-1 ITERATION 2: Gesture Handler
 * 
 * Advanced touch/mouse gesture support:
 * - Swipe detection
 * - Pinch zoom
 * - Long press
 * - Drag and drop
 * - Multi-touch gestures
 */

class GestureHandler {
    constructor(element, options = {}) {
        this.element = typeof element === 'string' ? document.querySelector(element) : element;

        this.options = {
            swipeThreshold: 50,
            swipeVelocity: 0.3,
            longPressDelay: 500,
            doubleTapDelay: 300,
            enableHaptics: true,
            ...options
        };

        this.state = {
            isDown: false,
            startX: 0,
            startY: 0,
            currentX: 0,
            currentY: 0,
            startTime: 0,
            lastTap: 0,
            longPressTimer: null,
            initialDistance: 0,
            initialAngle: 0
        };

        this.callbacks = {
            onSwipeLeft: [],
            onSwipeRight: [],
            onSwipeUp: [],
            onSwipeDown: [],
            onTap: [],
            onDoubleTap: [],
            onLongPress: [],
            onPinch: [],
            onRotate: [],
            onDragStart: [],
            onDrag: [],
            onDragEnd: []
        };

        this.init();
    }

    init() {
        if (!this.element) {
            console.warn('[GestureHandler] Element not found');
            return;
        }

        // Touch events
        this.element.addEventListener('touchstart', (e) => this.handleStart(e), { passive: false });
        this.element.addEventListener('touchmove', (e) => this.handleMove(e), { passive: false });
        this.element.addEventListener('touchend', (e) => this.handleEnd(e));
        this.element.addEventListener('touchcancel', (e) => this.handleEnd(e));

        // Mouse events for desktop
        this.element.addEventListener('mousedown', (e) => this.handleStart(e));
        this.element.addEventListener('mousemove', (e) => this.handleMove(e));
        this.element.addEventListener('mouseup', (e) => this.handleEnd(e));
        this.element.addEventListener('mouseleave', (e) => this.handleEnd(e));

        console.log('[GestureHandler] 👆 Gesture recognition active');
    }

    // Event registration
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
        return this; // Chainable
    }

    off(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event] = this.callbacks[event].filter(cb => cb !== callback);
        }
        return this;
    }

    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(cb => cb(data));
        }
    }

    // Touch coordinate extraction
    getCoords(e) {
        if (e.touches && e.touches.length > 0) {
            return {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY,
                touches: e.touches.length
            };
        }
        return {
            x: e.clientX,
            y: e.clientY,
            touches: 1
        };
    }

    // Multi-touch helpers
    getTouchDistance(touches) {
        if (touches.length < 2) return 0;
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.hypot(dx, dy);
    }

    getTouchAngle(touches) {
        if (touches.length < 2) return 0;
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.atan2(dy, dx) * (180 / Math.PI);
    }

    // Event handlers
    handleStart(e) {
        const coords = this.getCoords(e);

        this.state.isDown = true;
        this.state.startX = coords.x;
        this.state.startY = coords.y;
        this.state.currentX = coords.x;
        this.state.currentY = coords.y;
        this.state.startTime = Date.now();

        // Multi-touch initial state
        if (e.touches && e.touches.length >= 2) {
            this.state.initialDistance = this.getTouchDistance(e.touches);
            this.state.initialAngle = this.getTouchAngle(e.touches);
        }

        // Long press detection
        this.state.longPressTimer = setTimeout(() => {
            if (this.state.isDown) {
                this.emit('onLongPress', {
                    x: this.state.startX,
                    y: this.state.startY
                });
                this.hapticFeedback('heavy');
            }
        }, this.options.longPressDelay);

        // Drag start
        this.emit('onDragStart', {
            x: coords.x,
            y: coords.y,
            originalEvent: e
        });
    }

    handleMove(e) {
        if (!this.state.isDown) return;

        const coords = this.getCoords(e);

        // Cancel long press if moved
        const moveDistance = Math.hypot(
            coords.x - this.state.startX,
            coords.y - this.state.startY
        );

        if (moveDistance > 10 && this.state.longPressTimer) {
            clearTimeout(this.state.longPressTimer);
            this.state.longPressTimer = null;
        }

        // Multi-touch gestures
        if (e.touches && e.touches.length >= 2) {
            const currentDistance = this.getTouchDistance(e.touches);
            const currentAngle = this.getTouchAngle(e.touches);

            // Pinch
            const scale = currentDistance / this.state.initialDistance;
            this.emit('onPinch', { scale, center: coords });

            // Rotate
            const rotation = currentAngle - this.state.initialAngle;
            this.emit('onRotate', { rotation, center: coords });

            e.preventDefault();
        }

        this.state.currentX = coords.x;
        this.state.currentY = coords.y;

        // Drag
        this.emit('onDrag', {
            x: coords.x,
            y: coords.y,
            deltaX: coords.x - this.state.startX,
            deltaY: coords.y - this.state.startY,
            originalEvent: e
        });
    }

    handleEnd(e) {
        if (!this.state.isDown) return;

        // Clear long press timer
        if (this.state.longPressTimer) {
            clearTimeout(this.state.longPressTimer);
            this.state.longPressTimer = null;
        }

        const duration = Date.now() - this.state.startTime;
        const deltaX = this.state.currentX - this.state.startX;
        const deltaY = this.state.currentY - this.state.startY;
        const distance = Math.hypot(deltaX, deltaY);
        const velocity = distance / duration;

        // Swipe detection
        if (distance > this.options.swipeThreshold && velocity > this.options.swipeVelocity) {
            const angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI);

            if (angle > -45 && angle <= 45) {
                this.emit('onSwipeRight', { velocity, distance });
                this.hapticFeedback('light');
            } else if (angle > 45 && angle <= 135) {
                this.emit('onSwipeDown', { velocity, distance });
                this.hapticFeedback('light');
            } else if (angle > 135 || angle <= -135) {
                this.emit('onSwipeLeft', { velocity, distance });
                this.hapticFeedback('light');
            } else {
                this.emit('onSwipeUp', { velocity, distance });
                this.hapticFeedback('light');
            }
        }
        // Tap detection
        else if (distance < 10 && duration < 200) {
            const now = Date.now();

            // Double tap
            if (now - this.state.lastTap < this.options.doubleTapDelay) {
                this.emit('onDoubleTap', { x: this.state.currentX, y: this.state.currentY });
                this.hapticFeedback('medium');
                this.state.lastTap = 0;
            } else {
                this.emit('onTap', { x: this.state.currentX, y: this.state.currentY });
                this.hapticFeedback('light');
                this.state.lastTap = now;
            }
        }

        // Drag end
        this.emit('onDragEnd', {
            x: this.state.currentX,
            y: this.state.currentY,
            deltaX,
            deltaY,
            velocity
        });

        this.state.isDown = false;
    }

    // Haptic feedback (if supported)
    hapticFeedback(style = 'light') {
        if (!this.options.enableHaptics) return;

        if ('vibrate' in navigator) {
            const patterns = {
                light: [10],
                medium: [20],
                heavy: [30, 10, 30]
            };
            navigator.vibrate(patterns[style] || [10]);
        }
    }

    destroy() {
        this.element.removeEventListener('touchstart', this.handleStart);
        this.element.removeEventListener('touchmove', this.handleMove);
        this.element.removeEventListener('touchend', this.handleEnd);
        this.element.removeEventListener('touchcancel', this.handleEnd);
        this.element.removeEventListener('mousedown', this.handleStart);
        this.element.removeEventListener('mousemove', this.handleMove);
        this.element.removeEventListener('mouseup', this.handleEnd);
        this.element.removeEventListener('mouseleave', this.handleEnd);
    }
}

// Factory function for easy setup
function createGestureHandler(selector, options) {
    return new GestureHandler(selector, options);
}

// Setup gestures on provider cards
function setupCardGestures() {
    document.querySelectorAll('.provider-card').forEach(card => {
        const gesture = new GestureHandler(card);

        gesture
            .on('onTap', () => {
                card.classList.add('haptic-pop');
                setTimeout(() => card.classList.remove('haptic-pop'), 150);
            })
            .on('onDoubleTap', () => {
                // Toggle connection
                card.classList.toggle('connected');
                card.classList.add('haptic-bounce');
                setTimeout(() => card.classList.remove('haptic-bounce'), 500);
            })
            .on('onLongPress', () => {
                // Show context menu
                card.classList.add('haptic-pulse');
            })
            .on('onSwipeRight', () => {
                // Quick connect
                if (!card.classList.contains('connected')) {
                    card.style.transform = 'translateX(20px)';
                    setTimeout(() => {
                        card.style.transform = '';
                        card.classList.add('connected');
                    }, 200);
                }
            })
            .on('onSwipeLeft', () => {
                // Disconnect
                if (card.classList.contains('connected')) {
                    card.style.transform = 'translateX(-20px)';
                    setTimeout(() => {
                        card.style.transform = '';
                        card.classList.remove('connected');
                    }, 200);
                }
            });
    });
}

// Auto-init on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupCardGestures);
} else {
    setupCardGestures();
}

export { GestureHandler, createGestureHandler, setupCardGestures };
export default GestureHandler;
