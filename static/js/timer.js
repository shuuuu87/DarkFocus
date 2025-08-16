/**
 * DARKSULFOCUS - Local Storage Timer Management
 * Handles persistent timer state using browser local storage
 * Timers persist through page refreshes, navigation, and logouts
 */

class TimerManager {
    constructor() {
        this.timers = new Map();
        this.updateInterval = null;
        this.initialized = false;
        this.storageKey = 'darksulfocus_timers';
        this.isPageVisible = !document.hidden;
        this.backgroundStartTime = null;
        
        this.init();
    }

    init() {
        if (this.initialized) return;
        
        this.loadTimersFromStorage();
        this.findAndInitializeTimers();
        this.startUpdateLoop();
        this.setupEventListeners();
        
        this.initialized = true;
        console.log('Timer Manager initialized with local storage');
    }

    loadTimersFromStorage() {
        try {
            const storedTimers = localStorage.getItem(this.storageKey);
            if (storedTimers) {
                const timersData = JSON.parse(storedTimers);
                Object.entries(timersData).forEach(([taskId, timerData]) => {
                    let remainingSeconds = timerData.remainingSeconds;
                    // If endTimestamp is present and not paused, calculate remaining
                    if (timerData.endTimestamp && !timerData.isPaused) {
                        const now = Date.now();
                        remainingSeconds = Math.max(0, Math.ceil((timerData.endTimestamp - now) / 1000));
                    }
                    this.timers.set(taskId, {
                        ...timerData,
                        remainingSeconds: remainingSeconds,
                        lastUpdate: Date.now(),
                        element: null, // Will be set when DOM elements are found
                        taskItem: null
                    });
                });
                console.log(`Loaded ${this.timers.size} timers from local storage`);
            }
        } catch (error) {
            console.error('Error loading timers from storage:', error);
            localStorage.removeItem(this.storageKey);
        }
    }

    saveTimersToStorage() {
        try {
            const timersData = {};
            this.timers.forEach((timer, taskId) => {
                // Save endTimestamp if running, remainingSeconds if paused
                let timerData = {
                    isPaused: timer.isPaused,
                    totalDuration: timer.totalDuration,
                    title: timer.title,
                    lastUpdate: timer.lastUpdate
                };
                if (!timer.isPaused && timer.endTimestamp) {
                    timerData.endTimestamp = timer.endTimestamp;
                } else {
                    timerData.remainingSeconds = Math.ceil(timer.remainingSeconds);
                }
                timersData[taskId] = timerData;
            });
            localStorage.setItem(this.storageKey, JSON.stringify(timersData));
        } catch (error) {
            console.error('Error saving timers to storage:', error);
        }
    }

    findAndInitializeTimers() {
        const timerElements = document.querySelectorAll('.timer-display');
        
        timerElements.forEach(element => {
            const taskId = this.getTaskId(element);
            const taskItem = element.closest('.task-item');
            
            if (taskId) {
                // Check if timer exists in storage
                let timer = this.timers.get(taskId);
                
                if (!timer) {
                    // Create new timer from DOM data
                    const remainingSeconds = parseInt(element.dataset.remaining) || 0;
                    const titleElement = taskItem.querySelector('.task-title');
                    const durationElement = taskItem.querySelector('.task-duration');
                    
                    timer = {
                        remainingSeconds: remainingSeconds,
                        isPaused: true, // New timers start paused
                        lastUpdate: Date.now(),
                        totalDuration: remainingSeconds,
                        title: titleElement ? titleElement.textContent : 'Task',
                        element: element,
                        taskItem: taskItem
                    };
                    this.timers.set(taskId, timer);
                } else {
                    // Restore DOM references for existing timer
                    timer.element = element;
                    timer.taskItem = taskItem;
                }
                
                this.updateTimerDisplay(taskId);
                this.updateTimerVisualState(timer);
            }
        });
        
        // Clean up timers that no longer have DOM elements
        this.cleanupOrphanedTimers();
        
        console.log(`Initialized ${this.timers.size} timers`);
        this.saveTimersToStorage();
    }

    cleanupOrphanedTimers() {
        // Only cleanup if we're on a page that shows tasks
        const taskContainer = document.querySelector('.task-card, .tasks-container, .task-list, #active-tasks');
        if (!taskContainer) {
            // Not on a tasks page, don't cleanup timers
            return;
        }

        const activeTaskIds = new Set();
        document.querySelectorAll('.task-item').forEach(item => {
            const taskId = item.dataset.taskId;
            if (taskId) activeTaskIds.add(taskId);
        });

        // Only remove timers that don't have corresponding DOM elements on task pages
        for (const [taskId, timer] of this.timers.entries()) {
            if (!activeTaskIds.has(taskId)) {
                this.timers.delete(taskId);
                console.log(`Cleaned up orphaned timer: ${taskId}`);
            }
        }
    }

    getTaskId(element) {
        const taskItem = element.closest('.task-item');
        return taskItem ? taskItem.dataset.taskId : null;
    }

    startUpdateLoop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        this.updateInterval = setInterval(() => {
            this.updateActiveTimers();
        }, 1000);
    }

    // No server sync needed - using local storage only

    updateActiveTimers() {
        // Don't update timers if page is not visible to save battery
        if (!this.isPageVisible) {
            return;
        }
        
        const now = Date.now();
        let needsSave = false;
        this.timers.forEach((timer, taskId) => {
            if (!timer.isPaused && timer.endTimestamp && timer.remainingSeconds > 0) {
                const prevSeconds = Math.ceil(timer.remainingSeconds);
                timer.remainingSeconds = Math.max(0, Math.ceil((timer.endTimestamp - now) / 1000));
                timer.lastUpdate = now;
                // Only update DOM if value changed
                if (Math.ceil(timer.remainingSeconds) !== prevSeconds) {
                    this.updateTimerDisplay(taskId);
                }
                // Check if timer completed
                if (timer.remainingSeconds <= 0) {
                    this.handleTimerCompletion(taskId);
                }
            }
        });
    }

    updateTimerDisplay(taskId) {
        const timer = this.timers.get(taskId);
        if (!timer || !timer.element) return;
        // Only use integer seconds for display
        const intSeconds = Math.ceil(timer.remainingSeconds);
        const timeString = this.formatTime(intSeconds);
        timer.element.textContent = timeString;
        // Update visual state based on remaining time
        this.updateTimerVisualState(timer);
    }

    updateTimerVisualState(timer) {
        const element = timer.element;
        const taskItem = timer.taskItem;
        
        // Remove existing state classes
        element.classList.remove('timer-warning', 'timer-danger', 'timer-completed');
        taskItem?.classList.remove('paused');
        
        if (timer.remainingSeconds <= 0) {
            element.classList.add('timer-completed');
        } else if (timer.remainingSeconds <= 300) { // Last 5 minutes
            element.classList.add('timer-danger');
        } else if (timer.remainingSeconds <= 600) { // Last 10 minutes
            element.classList.add('timer-warning');
        }
        
        // Update pause state and button
        if (timer.isPaused) {
            taskItem?.classList.add('paused');
        } else {
            taskItem?.classList.remove('paused');
        }
        
        // Update the play/pause button
        this.updateControlButton(taskItem, timer.isPaused);
    }

    updateControlButton(taskItem, isPaused) {
        if (!taskItem) return;
        
        const controlsDiv = taskItem.querySelector('.task-controls');
        if (!controlsDiv) return;
        
        // Find the existing play/pause button
        const existingButton = controlsDiv.querySelector('.btn-success, .btn-warning, .btn-info');
        if (!existingButton) return;
        
        // Create new button based on state
        const newButton = document.createElement('a');
        newButton.href = '#';
        
        if (isPaused) {
            newButton.className = 'btn btn-success btn-sm';
            newButton.innerHTML = '<i class="fas fa-play"></i>';
            newButton.title = 'Start timer';
        } else {
            newButton.className = 'btn btn-warning btn-sm';
            newButton.innerHTML = '<i class="fas fa-pause"></i>';
            newButton.title = 'Pause timer';
        }
        
        // Replace the existing button
        existingButton.replaceWith(newButton);
    }

    handleTimerCompletion(taskId) {
        const timer = this.timers.get(taskId);
        if (!timer) return;
        
        console.log(`Timer ${taskId} completed`);
        
        // Stop the timer
        timer.isPaused = true;
        timer.remainingSeconds = 0;
        
        // Save to local storage
        this.saveTimersToStorage();
        
        // Update server about completion
        this.completeTask(taskId);
        
        // Show completion notification
        this.showCompletionNotification(taskId);
        
        // Play completion sound (if available)
        this.playCompletionSound();
    }

    async completeTask(taskId) {
        try {
            const response = await fetch(`/complete_task/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success && data.completed) {
                this.handleTaskCompleted(taskId, data.points_earned);
                console.log(`Task ${taskId} completed! Points earned: ${data.points_earned}`);
            } else {
                console.error(`Error completing task ${taskId}:`, data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error completing task:', error);
        }
    }

    handleTaskCompleted(taskId, pointsEarned) {
        // Remove timer from active timers
        this.timers.delete(taskId);
        
        // Remove task item from DOM
        const timer = this.timers.get(taskId);
        const taskItem = timer?.taskItem;
        if (taskItem) {
            taskItem.style.transition = 'opacity 0.5s ease';
            taskItem.style.opacity = '0';
            setTimeout(() => {
                taskItem.remove();
            }, 500);
        }
        
        // Show completion modal
        this.showCompletionModal(pointsEarned);
        
        // Update stats in UI
        this.updatePointsDisplay(pointsEarned);
    }

    showCompletionNotification(taskId, pointsEarned = 0) {
        // Browser notification
        if (window.DarkSulFocus?.showNotification) {
            window.DarkSulFocus.showNotification(
                'Task Completed!',
                `Congratulations! You earned ${pointsEarned.toFixed(1)} points.`,
                '/static/favicon.ico'
            );
        }
        
        // Toast notification
        if (window.DarkSulFocus?.showSuccessToast) {
            window.DarkSulFocus.showSuccessToast('Task completed successfully!');
        }
    }

    showCompletionModal(pointsEarned) {
        const modal = document.getElementById('timerCompleteModal');
        const pointsElement = document.getElementById('pointsEarned');
        
        if (modal && pointsElement) {
            pointsElement.textContent = `${pointsEarned.toFixed(1)} points`;
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    updatePointsDisplay(pointsEarned) {
        // Update total points display if visible
        const pointsDisplays = document.querySelectorAll('.stat-value, .points-display');
        pointsDisplays.forEach(element => {
            if (element.textContent.includes('points') || element.classList.contains('points-display')) {
                const currentPoints = parseFloat(element.textContent) || 0;
                const newPoints = currentPoints + pointsEarned;
                element.textContent = newPoints.toFixed(1);
            }
        });
    }

    playCompletionSound() {
        // Create and play completion sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.log('Audio notification not available:', error);
        }
    }

    // Local storage persistence - no server sync needed
    persistTimer(taskId) {
        this.saveTimersToStorage();
        console.log(`Timer ${taskId} persisted to local storage`);
    }

    pauseTimer(taskId) {
        const timer = this.timers.get(taskId);
        if (timer && !timer.isPaused) {
            // Pause server-side timer
            this.pauseServerTimer(taskId);
            
            // Calculate remainingSeconds from endTimestamp
            if (timer.endTimestamp) {
                timer.remainingSeconds = Math.max(0, Math.ceil((timer.endTimestamp - Date.now()) / 1000));
                delete timer.endTimestamp;
            }
            timer.isPaused = true;
            this.updateTimerVisualState(timer);
            this.saveTimersToStorage();
            console.log(`Timer ${taskId} paused`);
        }
    }

    resumeTimer(taskId) {
        const timer = this.timers.get(taskId);
        if (timer && timer.isPaused && timer.remainingSeconds > 0) {
            // Start server-side timer first
            this.startServerTimer(taskId);
            
            // Pause all other timers first (only one timer can run at a time)
            this.pauseAllTimers();
            timer.isPaused = false;
            timer.lastUpdate = Date.now();
            // Set endTimestamp for real-time tracking
            timer.endTimestamp = Date.now() + timer.remainingSeconds * 1000;
            
            // Remove any background state flags
            delete timer.wasRunningWhenBackgrounded;
            
            this.updateTimerVisualState(timer);
            this.saveTimersToStorage();
            console.log(`Timer ${taskId} resumed - running continuously on server`);
        }
    }
    
    async startServerTimer(taskId) {
        try {
            const response = await fetch(`/start_server_timer/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (data.success) {
                console.log(`Server timer started for task ${taskId}`);
            }
        } catch (error) {
            console.error('Error starting server timer:', error);
        }
    }
    
    async pauseServerTimer(taskId) {
        try {
            const response = await fetch(`/pause_server_timer/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (data.success) {
                console.log(`Server timer paused for task ${taskId}`);
            }
        } catch (error) {
            console.error('Error pausing server timer:', error);
        }
    }
    
    async checkServerCompletion(taskId) {
        try {
            const response = await fetch(`/get_timer_status/${taskId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (data.success && data.completed) {
                // Server says task is completed
                console.log(`Server confirmed task ${taskId} completed with ${data.points_earned} points`);
                this.handleServerCompletion(taskId, data.points_earned);
                return true;
            } else if (data.success && !data.completed && !data.is_completed) {
                // Task exists but not completed - update remaining time if different
                const timer = this.timers.get(taskId);
                if (timer && data.remaining_seconds !== undefined) {
                    timer.remainingSeconds = data.remaining_seconds;
                    this.updateTimerDisplay(taskId);
                }
            } else if (!data.success && data.error === 'Task not found') {
                // Task was deleted on server, remove from client
                console.log(`Task ${taskId} not found on server - removing from client`);
                this.timers.delete(taskId);
                this.saveTimersToStorage();
                return true; // Treat as completed to stop further processing
            }
            return false;
        } catch (error) {
            console.error('Error checking server completion:', error);
            return false;
        }
    }
    
    handleServerCompletion(taskId, pointsEarned) {
        console.log(`Task ${taskId} completed on server, points: ${pointsEarned}`);
        
        // Get timer reference before deleting
        const timer = this.timers.get(taskId);
        
        // Remove timer from local storage immediately
        this.timers.delete(taskId);
        this.saveTimersToStorage();
        
        // Show completion notification once
        this.showCompletionNotification(taskId, pointsEarned);
        
        // Remove task from DOM with animation
        if (timer?.taskItem) {
            timer.taskItem.style.transition = 'opacity 0.5s ease';
            timer.taskItem.style.opacity = '0';
            setTimeout(() => {
                if (timer.taskItem && timer.taskItem.parentNode) {
                    timer.taskItem.remove();
                }
            }, 500);
        }
        
        // Refresh page after a short delay to show updated stats
        setTimeout(() => {
            window.location.reload();
        }, 1500);
        
        // Play completion sound
        this.playCompletionSound();
    }

    pauseAllTimers() {
        this.timers.forEach((timer, taskId) => {
            if (!timer.isPaused) {
                timer.isPaused = true;
                this.updateTimerVisualState(timer);
            }
        });
        this.saveTimersToStorage();
    }

    removeTimer(taskId) {
        this.timers.delete(taskId);
        this.saveTimersToStorage();
    }

    // Create a new timer (when adding tasks)
    createTimer(taskId, durationMinutes, title) {
        const timer = {
            remainingSeconds: durationMinutes * 60,
            isPaused: true,
            lastUpdate: Date.now(),
            totalDuration: durationMinutes * 60,
            title: title,
            element: null,
            taskItem: null
            // endTimestamp will be set on resume
        };
        this.timers.set(taskId, timer);
        this.saveTimersToStorage();
        return timer;
    }

    // Reset a timer to its original duration
    resetTimer(taskId) {
        const timer = this.timers.get(taskId);
        if (timer) {
            timer.remainingSeconds = timer.totalDuration;
            timer.isPaused = true;
            timer.lastUpdate = Date.now();
            this.updateTimerDisplay(taskId);
            this.updateTimerVisualState(timer);
            this.saveTimersToStorage();
        }
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    getCSRFToken() {
        const tokenElement = document.querySelector('meta[name=csrf-token]') || 
                            document.querySelector('input[name=csrf_token]');
        return tokenElement ? tokenElement.content || tokenElement.value : '';
    }

    setupEventListeners() {
        // Listen for task control button clicks
        document.addEventListener('click', (e) => {
            const taskItem = e.target.closest('.task-item');
            if (!taskItem) return;
            
            const taskId = taskItem.dataset.taskId;
            if (!taskId) return;
            
            // Handle pause/resume buttons
            if (e.target.closest('.btn-warning, .btn-success')) {
                e.preventDefault(); // Prevent default link behavior
                const timer = this.timers.get(taskId);
                if (timer && timer.isPaused) {
                    this.resumeTimer(taskId);
                } else if (timer) {
                    this.pauseTimer(taskId);
                }
            }
            
            // Handle delete button
            if (e.target.closest('.btn-danger')) {
                this.removeTimer(taskId);
            }
        });
        
        // Enhanced mobile-friendly page visibility handling
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Additional mobile browser events for better detection
        window.addEventListener('blur', () => {
            this.handlePageBackgrounded();
        });
        
        window.addEventListener('focus', () => {
            this.handlePageForegrounded();
        });
        
        // Mobile Safari specific events
        window.addEventListener('pagehide', () => {
            this.handlePageBackgrounded();
        });
        
        window.addEventListener('pageshow', () => {
            this.handlePageForegrounded();
        });
        
        // Save timers before page unload
        window.addEventListener('beforeunload', () => {
            this.saveTimersToStorage();
        });
        
        // Force check for completed timers on any interaction
        ['touchstart', 'click', 'keydown'].forEach(eventType => {
            document.addEventListener(eventType, () => {
                this.checkForCompletedTimers();
            }, { passive: true });
        });
    }

    handleVisibilityChange() {
        if (document.visibilityState === 'visible') {
            this.handlePageForegrounded();
        } else {
            this.handlePageBackgrounded();
        }
    }
    
    handlePageBackgrounded() {
        console.log('Page backgrounded - timers continue running on server');
        this.isPageVisible = false;
        this.backgroundStartTime = Date.now();
        
        // DON'T pause timers - let them continue running on server
        // Just stop client-side display updates to save battery
        this.saveTimersToStorage();
    }
    
    handlePageForegrounded() {
        console.log('Page foregrounded - checking for completed timers');
        this.isPageVisible = true;
        
        const now = Date.now();
        const backgroundDuration = this.backgroundStartTime ? 
            Math.floor((now - this.backgroundStartTime) / 1000) : 0;
        
        if (backgroundDuration > 0) {
            console.log(`Was in background for ${backgroundDuration} seconds`);
        }
        
        // Check for server-side completed timers first
        this.checkForCompletedTimers();
        
        // Update timer displays
        this.findAndInitializeTimers();
        
        this.backgroundStartTime = null;
        this.saveTimersToStorage();
    }
    
    async checkForCompletedTimers() {
        let hasCompletedTimers = false;
        const now = Date.now();
        
        // Create array copy to avoid modification during iteration
        const timerEntries = Array.from(this.timers.entries());
        
        // Check all timers for completion
        for (const [taskId, timer] of timerEntries) {
            // Skip if timer was already removed
            if (!this.timers.has(taskId)) {
                continue;
            }
            
            // First check server-side completion
            const serverCompleted = await this.checkServerCompletion(taskId);
            if (serverCompleted) {
                hasCompletedTimers = true;
                continue; // Server handled completion, skip client-side checks
            }
            
            // Then check client-side completion only if server didn't complete it
            if (this.timers.has(taskId)) { // Double-check timer still exists
                // Check if timer was supposed to complete while in background
                if (timer.endTimestamp && timer.endTimestamp <= now) {
                    console.log(`Found client-side completed timer: ${taskId}`);
                    hasCompletedTimers = true;
                    timer.remainingSeconds = 0;
                    timer.isPaused = true;
                    delete timer.endTimestamp;
                    
                    // Trigger completion immediately
                    setTimeout(() => {
                        if (this.timers.has(taskId)) { // Final check before completion
                            this.handleTimerCompletion(taskId);
                        }
                    }, 100);
                }
                // Also check for paused timers with 0 remaining time
                else if (timer.isPaused && timer.remainingSeconds <= 0) {
                    console.log(`Found paused completed timer: ${taskId}`);
                    hasCompletedTimers = true;
                    setTimeout(() => {
                        if (this.timers.has(taskId)) { // Final check before completion
                            this.handleTimerCompletion(taskId);
                        }
                    }, 100);
                }
            }
        }
        
        return hasCompletedTimers;
    }

    destroy() {
        // Save timers before destroying
        this.saveTimersToStorage();
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        // Don't clear timers - they're saved in local storage
        this.initialized = false;
    }
    
    // Clear all stored timers (for logout or manual reset)
    clearAllTimers() {
        this.timers.clear();
        localStorage.removeItem(this.storageKey);
        console.log('All timers cleared from local storage');
    }
}

// Initialize timer manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.timerManager = new TimerManager();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', function() {
    if (window.timerManager) {
        window.timerManager.destroy();
    }
});

// Export for global access
window.TimerManager = TimerManager;
