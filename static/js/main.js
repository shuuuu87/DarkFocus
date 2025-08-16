/**
 * DARKSULFOCUS - Main Application Enhancement JavaScript
 * Additional functionality for enhanced user experience
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    initializeAnimations();
    initializeProgressTracking();
    initializeRankSystem();
    initializeCompetitionFeatures();
    initializeProfileEnhancements();
});

/**
 * Chart Initialization and Management
 */
function initializeCharts() {
    // Progress chart is handled in progress.html template
    // This function can be extended for additional charts
    
    // Initialize mini charts for profile page if present
    initializeMiniCharts();
    
    // Initialize rank progress bars
    initializeRankProgressBars();
}

function initializeMiniCharts() {
    const miniChartElements = document.querySelectorAll('.mini-chart');
    
    miniChartElements.forEach(element => {
        const type = element.dataset.chartType;
        const data = JSON.parse(element.dataset.chartData || '[]');
        
        if (type === 'streak') {
            createStreakMiniChart(element, data);
        } else if (type === 'points') {
            createPointsMiniChart(element, data);
        }
    });
}

function createStreakMiniChart(element, data) {
    const canvas = element.querySelector('canvas');
    if (!canvas) return;
    
    new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                data: data.map(d => d.streak),
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false }
            },
            elements: { point: { radius: 0 } }
        }
    });
}

function createPointsMiniChart(element, data) {
    const canvas = element.querySelector('canvas');
    if (!canvas) return;
    
    new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                data: data.map(d => d.points),
                backgroundColor: '#00ff88',
                borderRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

/**
 * Rank Progress Bar Animation
 */
function initializeRankProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.transition = 'width 2s ease-in-out';
            bar.style.width = targetWidth;
        }, 500);
    });
}

/**
 * Enhanced Animations
 */
function initializeAnimations() {
    // Stagger card animations
    const cards = document.querySelectorAll('.card, .stat-card, .task-item');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Hover animations for interactive elements
    initializeHoverAnimations();
    
    // Scroll animations
    initializeScrollAnimations();
}

function initializeHoverAnimations() {
    // Enhanced button hover effects
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Card hover effects
    const hoverCards = document.querySelectorAll('.stat-card, .task-item, .rank-item');
    hoverCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px) scale(1.02)';
            this.style.boxShadow = '0 8px 25px rgba(0, 255, 136, 0.3)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = '';
        });
    });
}

function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for scroll animation
    const animateElements = document.querySelectorAll('.card, .stat-card, .rank-item');
    animateElements.forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
}

/**
 * Progress Tracking Enhancements
 */
function initializeProgressTracking() {
    // Real-time progress updates
    trackStudySession();
    
    // Daily goal tracking
    initializeDailyGoals();
    
    // Achievement notifications
    initializeAchievements();
}

function trackStudySession() {
    let sessionStartTime = Date.now();
    let totalSessionTime = 0;
    
    // Track active session time
    setInterval(() => {
        if (!document.hidden) {
            totalSessionTime += 1000; // Add 1 second
            updateSessionDisplay(totalSessionTime);
        }
    }, 1000);
    
    // Save session data on page unload
    window.addEventListener('beforeunload', () => {
        const sessionData = {
            date: new Date().toISOString().split('T')[0],
            duration: totalSessionTime,
            timestamp: Date.now()
        };
        
        window.DarkSulFocus?.saveToLocalStorage('lastSession', sessionData);
    });
}

function updateSessionDisplay(sessionTime) {
    const sessionDisplay = document.querySelector('.session-time');
    if (sessionDisplay) {
        const minutes = Math.floor(sessionTime / 60000);
        const seconds = Math.floor((sessionTime % 60000) / 1000);
        sessionDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

function initializeDailyGoals() {
    const dailyGoal = 120; // 2 hours in minutes
    const todayMinutes = getTodayStudyMinutes();
    
    updateDailyGoalProgress(todayMinutes, dailyGoal);
}

function getTodayStudyMinutes() {
    // This would typically come from the server
    // For now, extract from the page if available
    const todayElement = document.querySelector('[data-today-minutes]');
    return todayElement ? parseInt(todayElement.dataset.todayMinutes) : 0;
}

function updateDailyGoalProgress(current, goal) {
    const progressElements = document.querySelectorAll('.daily-goal-progress');
    progressElements.forEach(element => {
        const percentage = Math.min((current / goal) * 100, 100);
        const progressBar = element.querySelector('.progress-bar');
        const progressText = element.querySelector('.progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }
        
        if (progressText) {
            progressText.textContent = `${current}/${goal} minutes`;
        }
    });
}

/**
 * Rank System Enhancements
 */
function initializeRankSystem() {
    // Animated rank display
    animateRankDisplay();
    
    // Rank progression indicators
    initializeRankProgression();
    
    // Next rank calculator
    initializeNextRankCalculator();
}

function animateRankDisplay() {
    const rankElements = document.querySelectorAll('.stat-value, .rank-display');
    
    rankElements.forEach(element => {
        if (element.textContent.match(/^\d+\.?\d*$/)) {
            const finalValue = parseFloat(element.textContent);
            animateNumber(element, 0, finalValue, 2000);
        }
    });
}

function animateNumber(element, start, end, duration) {
    const startTime = Date.now();
    const difference = end - start;
    
    function update() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = easeOutCubic(progress);
        const current = start + (difference * easeProgress);
        
        element.textContent = current.toFixed(1);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = end.toFixed(1);
        }
    }
    
    update();
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

function initializeRankProgression() {
    const currentPoints = getCurrentUserPoints();
    const nextRankInfo = getNextRankInfo(currentPoints);
    
    if (nextRankInfo) {
        updateRankProgressionDisplay(currentPoints, nextRankInfo);
    }
}

function getCurrentUserPoints() {
    const pointsElement = document.querySelector('[data-user-points]');
    return pointsElement ? parseFloat(pointsElement.dataset.userPoints) : 0;
}

function getNextRankInfo(currentPoints) {
    const ranks = [
        { name: 'Dormant', min: 0, max: 100 },
        { name: 'Initiate', min: 101, max: 300 },
        { name: 'Grinder', min: 301, max: 600 },
        { name: 'Executor', min: 601, max: 1000 },
        { name: 'Obsessor', min: 1001, max: 1500 },
        { name: 'Disciplinar', min: 1501, max: 2000 },
        { name: 'Sentinel', min: 2001, max: 2600 },
        { name: 'Dominus', min: 2601, max: 3300 },
        { name: 'Phantom', min: 3301, max: 4000 },
        { name: 'Apex Mind', min: 4001, max: 4700 },
        { name: 'System Override', min: 4701, max: 5500 },
        { name: 'Darkensul Core', min: 5501, max: Infinity }
    ];
    
    return ranks.find(rank => currentPoints < rank.max);
}

function updateRankProgressionDisplay(currentPoints, nextRank) {
    const progressionElements = document.querySelectorAll('.rank-progression');
    
    progressionElements.forEach(element => {
        const pointsNeeded = nextRank.max - currentPoints;
        const progressPercentage = ((currentPoints - nextRank.min) / (nextRank.max - nextRank.min)) * 100;
        
        element.innerHTML = `
            <div class="next-rank-info">
                <span class="next-rank-name">${nextRank.name}</span>
                <span class="points-needed">${pointsNeeded.toFixed(0)} points needed</span>
            </div>
            <div class="progress mt-2">
                <div class="progress-bar bg-primary" style="width: ${progressPercentage}%"></div>
            </div>
        `;
    });
}

function initializeNextRankCalculator() {
    const calculatorElements = document.querySelectorAll('.next-rank-calculator');
    
    calculatorElements.forEach(element => {
        const button = element.querySelector('.calculate-btn');
        const display = element.querySelector('.calculation-result');
        
        if (button && display) {
            button.addEventListener('click', () => {
                const currentPoints = getCurrentUserPoints();
                const nextRank = getNextRankInfo(currentPoints);
                
                if (nextRank) {
                    const pointsNeeded = nextRank.max - currentPoints;
                    const minutesNeeded = Math.ceil(pointsNeeded / 0.083333);
                    const hoursNeeded = Math.ceil(minutesNeeded / 60);
                    const daysNeeded = Math.ceil(hoursNeeded / 2); // Assuming 2 hours per day
                    
                    display.innerHTML = `
                        <div class="calculation-breakdown">
                            <p><strong>To reach ${nextRank.name}:</strong></p>
                            <ul>
                                <li>${pointsNeeded.toFixed(1)} points needed</li>
                                <li>${minutesNeeded} minutes of study</li>
                                <li>${hoursNeeded} hours of study</li>
                                <li>~${daysNeeded} days at 2h/day</li>
                            </ul>
                        </div>
                    `;
                }
            });
        }
    });
}

/**
 * Competition Feature Enhancements
 */
function initializeCompetitionFeatures() {
    // Real-time competition updates
    initializeCompetitionUpdates();
    
    // Challenge validation
    initializeChallengeValidation();
    
    // Competition statistics
    initializeCompetitionStats();
}

function initializeCompetitionUpdates() {
    // Check for active competitions periodically
    setInterval(() => {
        updateActiveCompetitions();
    }, 60000); // Check every minute
}

function updateActiveCompetitions() {
    const activeCompetitions = document.querySelectorAll('.active-competition');
    
    activeCompetitions.forEach(competition => {
        const endTime = new Date(competition.dataset.endTime);
        const now = new Date();
        const timeLeft = endTime - now;
        
        if (timeLeft > 0) {
            updateCompetitionCountdown(competition, timeLeft);
        } else {
            markCompetitionEnded(competition);
        }
    });
}

function updateCompetitionCountdown(element, timeLeft) {
    const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    
    const countdownElement = element.querySelector('.competition-countdown');
    if (countdownElement) {
        countdownElement.textContent = `${days}d ${hours}h ${minutes}m left`;
    }
}

function markCompetitionEnded(element) {
    element.classList.add('competition-ended');
    const countdownElement = element.querySelector('.competition-countdown');
    if (countdownElement) {
        countdownElement.textContent = 'Competition ended';
    }
}

function initializeChallengeValidation() {
    const challengeForms = document.querySelectorAll('.challenge-form');
    
    challengeForms.forEach(form => {
        const usernameInput = form.querySelector('input[name="opponent_username"]');
        
        if (usernameInput) {
            usernameInput.addEventListener('input', debounce(validateUsername, 500));
        }
    });
}

function validateUsername(event) {
    const username = event.target.value.trim();
    const feedback = event.target.parentNode.querySelector('.username-feedback');
    
    if (username.length < 3) {
        showUsernameFeedback(feedback, 'Username must be at least 3 characters', 'invalid');
        return;
    }
    
    // Here you could add an AJAX call to check username existence
    // For now, just show a generic validation message
    showUsernameFeedback(feedback, 'Username format is valid', 'valid');
}

function showUsernameFeedback(element, message, type) {
    if (!element) {
        element = document.createElement('div');
        element.className = 'username-feedback small mt-1';
    }
    
    element.textContent = message;
    element.className = `username-feedback small mt-1 text-${type === 'valid' ? 'success' : 'danger'}`;
}

function initializeCompetitionStats() {
    // Calculate and display competition statistics
    const statsElements = document.querySelectorAll('.competition-stats');
    
    statsElements.forEach(element => {
        calculateCompetitionStats(element);
    });
}

function calculateCompetitionStats(element) {
    const challenges = document.querySelectorAll('.challenge-item');
    const stats = {
        total: challenges.length,
        won: 0,
        lost: 0,
        pending: 0,
        active: 0
    };
    
    challenges.forEach(challenge => {
        const status = challenge.dataset.status;
        const winner = challenge.dataset.winner;
        const currentUserId = challenge.dataset.currentUserId;
        
        if (status === 'pending') stats.pending++;
        else if (status === 'active') stats.active++;
        else if (status === 'completed') {
            if (winner === currentUserId) stats.won++;
            else stats.lost++;
        }
    });
    
    element.innerHTML = `
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">${stats.total}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-item">
                <div class="stat-value text-success">${stats.won}</div>
                <div class="stat-label">Won</div>
            </div>
            <div class="stat-item">
                <div class="stat-value text-danger">${stats.lost}</div>
                <div class="stat-label">Lost</div>
            </div>
            <div class="stat-item">
                <div class="stat-value text-warning">${stats.active}</div>
                <div class="stat-label">Active</div>
            </div>
        </div>
    `;
}

/**
 * Profile Enhancement Features
 */
function initializeProfileEnhancements() {
    // Profile image preview
    initializeImagePreview();
    
    // Form validation enhancements
    initializeAdvancedValidation();
    
    // Profile completion tracker
    initializeProfileCompletion();
}

function initializeImagePreview() {
    const imageInput = document.querySelector('input[type="file"][name="profile_image"]');
    
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    showImagePreview(e.target.result);
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

function showImagePreview(imageSrc) {
    let preview = document.querySelector('.image-preview');
    
    if (!preview) {
        preview = document.createElement('div');
        preview.className = 'image-preview mt-2';
        
        const imageInput = document.querySelector('input[type="file"][name="profile_image"]');
        imageInput.parentNode.appendChild(preview);
    }
    
    preview.innerHTML = `
        <img src="${imageSrc}" alt="Preview" class="img-thumbnail" style="max-width: 150px; max-height: 150px;">
        <button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="clearImagePreview()">
            <i class="fas fa-times"></i> Remove
        </button>
    `;
}

function clearImagePreview() {
    const preview = document.querySelector('.image-preview');
    const imageInput = document.querySelector('input[type="file"][name="profile_image"]');
    
    if (preview) preview.remove();
    if (imageInput) imageInput.value = '';
}

function initializeAdvancedValidation() {
    // Password strength meter
    const passwordInput = document.querySelector('input[name="new_password"]');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            updatePasswordStrength(this.value);
        });
    }
    
    // Email format validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateEmailFormat(this);
        });
    });
}

function updatePasswordStrength(password) {
    const strength = calculatePasswordStrength(password);
    const meter = getOrCreatePasswordMeter();
    
    meter.className = `password-strength-meter strength-${strength.level}`;
    meter.innerHTML = `
        <div class="strength-bar">
            <div class="strength-fill" style="width: ${strength.percentage}%"></div>
        </div>
        <div class="strength-text">${strength.text}</div>
    `;
}

function calculatePasswordStrength(password) {
    let score = 0;
    
    if (password.length >= 8) score += 25;
    if (password.match(/[a-z]/)) score += 25;
    if (password.match(/[A-Z]/)) score += 25;
    if (password.match(/[0-9]/)) score += 15;
    if (password.match(/[^a-zA-Z0-9]/)) score += 10;
    
    let level = 'weak';
    let text = 'Weak';
    
    if (score >= 80) {
        level = 'strong';
        text = 'Strong';
    } else if (score >= 60) {
        level = 'medium';
        text = 'Medium';
    }
    
    return { level, text, percentage: Math.min(score, 100) };
}

function getOrCreatePasswordMeter() {
    let meter = document.querySelector('.password-strength-meter');
    
    if (!meter) {
        meter = document.createElement('div');
        meter.className = 'password-strength-meter mt-2';
        
        const passwordInput = document.querySelector('input[name="new_password"]');
        passwordInput.parentNode.appendChild(meter);
    }
    
    return meter;
}

function validateEmailFormat(input) {
    const email = input.value.trim();
    const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    
    input.classList.remove('is-valid', 'is-invalid');
    
    if (email && !isValid) {
        input.classList.add('is-invalid');
    } else if (email && isValid) {
        input.classList.add('is-valid');
    }
}

function initializeProfileCompletion() {
    const completionItems = [
        { selector: 'input[name="username"]', label: 'Username set' },
        { selector: 'input[name="email"]', label: 'Email verified' },
        { selector: '.profile-image', label: 'Profile image' },
        { selector: '.user-bio', label: 'Bio added' }
    ];
    
    const completedItems = completionItems.filter(item => {
        const element = document.querySelector(item.selector);
        return element && element.value && element.value.trim();
    });
    
    const completionPercentage = Math.round((completedItems.length / completionItems.length) * 100);
    updateProfileCompletionDisplay(completionPercentage, completedItems, completionItems);
}

function updateProfileCompletionDisplay(percentage, completed, total) {
    const completionElement = document.querySelector('.profile-completion');
    
    if (completionElement) {
        completionElement.innerHTML = `
            <h6>Profile Completion</h6>
            <div class="progress mb-2">
                <div class="progress-bar bg-primary" style="width: ${percentage}%"></div>
            </div>
            <small class="text-muted">${completed.length}/${total.length} sections completed (${percentage}%)</small>
        `;
    }
}

/**
 * Utility Functions
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global access
window.DarkSulFocusMain = {
    initializeCharts,
    initializeAnimations,
    initializeProgressTracking,
    initializeRankSystem,
    initializeCompetitionFeatures,
    initializeProfileEnhancements,
    animateNumber,
    clearImagePreview,
    calculatePasswordStrength,
    validateEmailFormat
};
