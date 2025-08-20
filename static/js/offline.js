/**
 * DARKSULFOCUS - Offline Functionality Manager
 * Handles offline data storage, sync, and UI updates
 */

class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineData = {
            tasks: [],
            completedTasks: [],
            points: 0,
            lastSync: null
        };
        this.storageKey = 'darksulfocus_offline_data';
        this.init();
    }

    init() {
        this.loadOfflineData();
        this.setupEventListeners();
        this.registerServiceWorker();
        this.updateOnlineStatus();
    }

    // Register service worker for caching
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered successfully:', registration);
                
                // Listen for service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    if (newWorker) {
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                this.showUpdateAvailable();
                            }
                        });
                    }
                });
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    // Setup online/offline event listeners
    setupEventListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateOnlineStatus();
            this.syncWhenOnline();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateOnlineStatus();
        });

        // Intercept form submissions for offline storage
        document.addEventListener('submit', (e) => {
            if (!this.isOnline && e.target.matches('form')) {
                e.preventDefault();
                this.handleOfflineFormSubmission(e.target);
            }
        });
    }

    // Update UI based on online status
    updateOnlineStatus() {
        const statusIndicator = this.createStatusIndicator();
        
        // Remove existing indicator
        const existingIndicator = document.querySelector('.offline-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // Add new indicator
        document.body.appendChild(statusIndicator);

        // Update navigation links for offline mode
        this.updateNavigationForOffline();
    }

    createStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.className = `offline-indicator ${this.isOnline ? 'online' : 'offline'}`;
        indicator.innerHTML = `
            <div class="status-content">
                <i class="fas ${this.isOnline ? 'fa-wifi' : 'fa-wifi-slash'}"></i>
                <span>${this.isOnline ? 'Online' : 'Offline Mode'}</span>
                ${!this.isOnline ? '<small>Changes will sync when back online</small>' : ''}
            </div>
        `;
        
        // Add styles
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1050;
            padding: 10px 15px;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            ${this.isOnline ? 
                'background: linear-gradient(135deg, #28a745, #20c997);' : 
                'background: linear-gradient(135deg, #ffc107, #fd7e14);'
            }
        `;

        return indicator;
    }

    // Handle form submissions when offline
    handleOfflineFormSubmission(form) {
        const formData = new FormData(form);
        const action = form.action;

        // Handle different types of forms
        if (action.includes('/add_task')) {
            this.addTaskOffline(formData);
        } else if (action.includes('/complete_task')) {
            this.completeTaskOffline(formData);
        }

        this.showOfflineMessage('Changes saved offline. Will sync when back online.');
    }

    // Add task offline
    addTaskOffline(formData) {
        const task = {
            id: 'offline_' + Date.now(),
            title: formData.get('title'),
            duration_minutes: parseInt(formData.get('duration_minutes')),
            created_at: new Date().toISOString(),
            status: 'pending',
            offline: true
        };

        this.offlineData.tasks.push(task);
        this.saveOfflineData();
        this.addTaskToDOM(task);
    }

    // Complete task offline
    completeTaskOffline(formData) {
        const taskId = formData.get('task_id');
        const timeSpent = parseInt(formData.get('time_spent_minutes') || 0);
        
        // Calculate points (same logic as server)
        const points = this.calculatePoints(timeSpent);
        
        const completedTask = {
            id: taskId,
            time_spent_minutes: timeSpent,
            points: points,
            completed_at: new Date().toISOString(),
            offline: true
        };

        this.offlineData.completedTasks.push(completedTask);
        this.offlineData.points += points;
        this.saveOfflineData();
        
        // Update UI
        this.removeTaskFromDOM(taskId);
        this.updatePointsDisplay(points);
        this.showOfflineMessage(`Task completed! +${points} points (offline)`);
    }

    // Calculate points for completed task
    calculatePoints(timeSpentMinutes) {
        if (timeSpentMinutes <= 0) return 0;
        
        let points = timeSpentMinutes * 2; // Base points
        
        // Bonus for longer sessions
        if (timeSpentMinutes >= 60) {
            points += 20; // 1 hour bonus
        }
        if (timeSpentMinutes >= 120) {
            points += 30; // 2 hour bonus
        }
        
        return Math.round(points);
    }

    // Add task to DOM
    addTaskToDOM(task) {
        const tasksList = document.querySelector('.tasks-list, .row .col-12:last-child .card-body');
        if (!tasksList) return;

        const taskElement = document.createElement('div');
        taskElement.className = 'task-item card mb-3 offline-task';
        taskElement.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${task.title}</h6>
                        <small class="text-muted">${task.duration_minutes} minutes</small>
                        <span class="badge bg-warning ms-2">Offline</span>
                    </div>
                    <div class="timer-controls">
                        <button class="btn btn-primary btn-sm start-timer" data-task-id="${task.id}">
                            <i class="fas fa-play"></i> Start
                        </button>
                    </div>
                </div>
            </div>
        `;

        tasksList.appendChild(taskElement);
    }

    // Remove task from DOM
    removeTaskFromDOM(taskId) {
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`)?.closest('.task-item');
        if (taskElement) {
            taskElement.remove();
        }
    }

    // Update points display
    updatePointsDisplay(additionalPoints) {
        const pointsElement = document.querySelector('.stat-value');
        if (pointsElement) {
            const currentPoints = parseFloat(pointsElement.textContent) || 0;
            const newPoints = currentPoints + additionalPoints;
            pointsElement.textContent = newPoints.toFixed(1);
        }
    }

    // Load offline data from localStorage
    loadOfflineData() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                this.offlineData = { ...this.offlineData, ...JSON.parse(stored) };
            }
        } catch (error) {
            console.error('Error loading offline data:', error);
        }
    }

    // Save offline data to localStorage
    saveOfflineData() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.offlineData));
        } catch (error) {
            console.error('Error saving offline data:', error);
        }
    }

    // Sync offline data when back online
    async syncWhenOnline() {
        if (!this.isOnline || this.isSyncing) return;

        this.isSyncing = true;
        this.showOfflineMessage('Syncing offline changes...', 'info');

        try {
            // Sync tasks
            for (const task of this.offlineData.tasks) {
                if (task.offline) {
                    await this.syncTask(task);
                }
            }

            // Sync completed tasks
            for (const completedTask of this.offlineData.completedTasks) {
                if (completedTask.offline) {
                    await this.syncCompletedTask(completedTask);
                }
            }

            // Clear synced data
            this.offlineData.tasks = this.offlineData.tasks.filter(t => !t.offline);
            this.offlineData.completedTasks = this.offlineData.completedTasks.filter(t => !t.offline);
            this.offlineData.lastSync = new Date().toISOString();
            this.saveOfflineData();

            this.showOfflineMessage('All changes synced successfully!', 'success');
            
            // Reload page to get fresh data
            setTimeout(() => window.location.reload(), 2000);
            
        } catch (error) {
            console.error('Sync failed:', error);
            this.showOfflineMessage('Sync failed. Will retry later.', 'error');
        } finally {
            this.isSyncing = false;
        }
    }

    // Sync individual task
    async syncTask(task) {
        const formData = new FormData();
        formData.append('title', task.title);
        formData.append('duration_minutes', task.duration_minutes);
        formData.append('csrf_token', this.getCSRFToken());

        const response = await fetch('/add_task', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to sync task');
        }
    }

    // Sync completed task
    async syncCompletedTask(completedTask) {
        const formData = new FormData();
        formData.append('task_id', completedTask.id);
        formData.append('time_spent_minutes', completedTask.time_spent_minutes);
        formData.append('csrf_token', this.getCSRFToken());

        const response = await fetch('/complete_task', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to sync completed task');
        }
    }

    // Get CSRF token from page
    getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }

    // Show offline message
    showOfflineMessage(message, type = 'warning') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show offline-alert`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 1040;
            max-width: 300px;
        `;

        document.body.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Update navigation for offline mode
    updateNavigationForOffline() {
        const navLinks = document.querySelectorAll('.sidebar-menu a');
        navLinks.forEach(link => {
            if (!this.isOnline) {
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && !this.isCachedRoute(href)) {
                    link.style.opacity = '0.5';
                    link.style.pointerEvents = 'none';
                    link.title = 'Available when online';
                }
            } else {
                link.style.opacity = '';
                link.style.pointerEvents = '';
                link.title = '';
            }
        });
    }

    // Check if route is cached for offline access
    isCachedRoute(href) {
        const cachedRoutes = ['/', '/profile', '/progress', '/help'];
        return cachedRoutes.some(route => href.includes(route));
    }

    // Show update available notification
    showUpdateAvailable() {
        const updateDiv = document.createElement('div');
        updateDiv.className = 'alert alert-info alert-dismissible fade show';
        updateDiv.innerHTML = `
            App update available! 
            <button type="button" class="btn btn-sm btn-primary ms-2" onclick="window.location.reload()">
                Update Now
            </button>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        updateDiv.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1040;
            max-width: 300px;
        `;

        document.body.appendChild(updateDiv);
    }
}

// Initialize offline manager when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    window.offlineManager = new OfflineManager();
});

// Export for other scripts
window.OfflineManager = OfflineManager;