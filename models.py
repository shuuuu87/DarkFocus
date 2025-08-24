from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pytz

class User(UserMixin, db.Model):
    last_active = db.Column(db.DateTime)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_image = db.Column(db.String(200), default='default.png')
    total_points = db.Column(db.Float, default=0.0)
    current_streak = db.Column(db.Integer, default=0)
    max_streak = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date)
    grace_days_used = db.Column(db.Integer, default=0)
    total_study_time = db.Column(db.Integer, default=0)  # in minutes
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Email preferences
    email_notifications = db.Column(db.Boolean, default=True)
    daily_reminders = db.Column(db.Boolean, default=True)
    weekly_summaries = db.Column(db.Boolean, default=True)
    achievement_emails = db.Column(db.Boolean, default=True)
    challenge_emails = db.Column(db.Boolean, default=True)
    
    # Relationships
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    sent_challenges = db.relationship('Challenge', foreign_keys='Challenge.challenger_id', backref='challenger', lazy=True)
    received_challenges = db.relationship('Challenge', foreign_keys='Challenge.challenged_id', backref='challenged', lazy=True)
    daily_stats = db.relationship('DailyStats', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_rank(self):
        points = self.total_points
        if points < 101:
            return "Dormant"
        elif points < 301:
            return "Initiate"
        elif points < 601:
            return "Grinder"
        elif points < 1001:
            return "Executor"
        elif points < 1501:
            return "Obsessor"
        elif points < 2001:
            return "Disciplinar"
        elif points < 2601:
            return "Sentinel"
        elif points < 3301:
            return "Dominus"
        elif points < 4001:
            return "Phantom"
        elif points < 4701:
            return "Apex Mind"
        elif points < 5501:
            return "System Override"
        else:
            return "Darkensul Core"
    
    def get_rank_progress(self):
        points = self.total_points
        thresholds = [101, 301, 601, 1001, 1501, 2001, 2601, 3301, 4001, 4701, 5501]
        
        for i, threshold in enumerate(thresholds):
            if points < threshold:
                prev_threshold = thresholds[i-1] if i > 0 else 0
                progress = points - prev_threshold
                total = threshold - prev_threshold
                return f"Progress: {progress:.0f} / {total} points"
        
        return f"Progress: {points:.0f} / ∞ points"
    
    def check_and_update_streak(self):
        """Check if streak should be broken due to missed days"""
        if not self.last_study_date:
            return
            
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).date()
        days_since_last_study = (today - self.last_study_date).days
        
        # Break streak if user hasn't studied for 3 or more consecutive days (2+ day gap)
        if days_since_last_study >= 3:
            self.current_streak = 0
            self.grace_days_used = 0
            
    def update_streak(self, study_minutes_today):
        """Update streak when user completes study session"""
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).date()

        # Initialize fields if they don't exist
        if not hasattr(self, 'grace_days_used') or self.grace_days_used is None:
            self.grace_days_used = 0

        # Minimum study time requirement (120 minutes)
        if study_minutes_today >= 120:
            if self.last_study_date:
                days_diff = (today - self.last_study_date).days

                if days_diff == 0:
                    # Same day - don't change streak, just update study date
                    pass
                elif days_diff == 1:
                    # Consecutive day - increment streak
                    self.current_streak += 1
                elif days_diff == 2:
                    # 1-day gap - check if grace days available
                    if self.grace_days_used < 3:  # Allow 3 grace days per streak
                        self.grace_days_used += 1
                        # Streak remains unchanged - grace period used
                        pass
                    else:
                        # No more grace days - streak is broken
                        self.current_streak = 1
                        self.grace_days_used = 0
                elif days_diff >= 3:
                    # 2+ day gap - streak is broken
                    self.current_streak = 1
                    self.grace_days_used = 0
            else:
                # First time studying or no previous study date
                self.current_streak = 1
                self.grace_days_used = 0

            self.last_study_date = today
            if not self.max_streak:
                self.max_streak = 0
            if self.current_streak > self.max_streak:
                self.max_streak = self.current_streak
                
    @staticmethod
    def check_all_users_streaks():
        """Check and update streaks for all users - called daily by background service"""
        users = User.query.all()
        for user in users:
            user.check_and_update_streak()
        db.session.commit()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Server-side timer tracking for true background timers
    started_at = db.Column(db.DateTime)
    expected_completion = db.Column(db.DateTime)  # When timer should complete
    is_active = db.Column(db.Boolean, default=False)  # Is timer currently running
    
    def get_time_display(self):
        total_seconds = self.duration_minutes * 60
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def start_timer(self):
        """Start the server-side timer"""
        self.is_active = True
        self.started_at = datetime.utcnow()
        self.expected_completion = datetime.utcnow() + timedelta(minutes=self.duration_minutes)
        
    def pause_timer(self):
        """Pause the server-side timer and calculate remaining time"""
        if self.is_active and self.started_at:
            # Calculate how much time has elapsed
            elapsed_minutes = (datetime.utcnow() - self.started_at).total_seconds() / 60
            # Update duration_minutes to remaining time
            self.duration_minutes = max(0, int(self.duration_minutes - elapsed_minutes))
            self.is_active = False
            self.started_at = None
            self.expected_completion = None
    
    def get_remaining_seconds(self):
        """Get remaining seconds for active timer"""
        if not self.is_active or not self.expected_completion:
            return self.duration_minutes * 60
            
        remaining = (self.expected_completion - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    def is_timer_completed(self):
        """Check if timer should be completed"""
        if self.is_completed or not self.is_active:
            return False
            
        return self.expected_completion is not None and datetime.utcnow() >= self.expected_completion
    
    def complete_task(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            
            # Calculate points earned
            total_minutes = self.duration_minutes
            points_earned = total_minutes * 0.083333  # 1/12 point per minute
            
            # Add points to user
            user = db.session.get(User, self.user_id)
            if user:
                user.total_points += points_earned
            
            # Update active challenges with points earned during challenge period
            active_challenges = Challenge.query.filter(
                Challenge.status == 'active',
                Challenge.start_date <= datetime.utcnow(),
                Challenge.end_date > datetime.utcnow()
            ).filter(
                (Challenge.challenger_id == self.user_id) | (Challenge.challenged_id == self.user_id)
            ).all()
            
            for challenge in active_challenges:
                if challenge.challenger_id == self.user_id:
                    challenge.challenger_points += points_earned
                elif challenge.challenged_id == self.user_id:
                    challenge.challenged_points += points_earned
            
            # Update daily stats
            ist = pytz.timezone('Asia/Kolkata')
            today = datetime.now(ist).date()
            daily_stat = DailyStats.query.filter_by(user_id=self.user_id, date=today).first()
            
            if not daily_stat:
                daily_stat = DailyStats()
                daily_stat.user_id = self.user_id
                daily_stat.date = today
                daily_stat.minutes_studied = 0
                daily_stat.tasks_completed = 0
                daily_stat.points_earned = 0.0
                db.session.add(daily_stat)
            
            daily_stat.minutes_studied += total_minutes
            daily_stat.tasks_completed += 1
            daily_stat.points_earned += points_earned
            
            # Update user's total study time and streak
            if user:
                user.total_study_time += total_minutes
                # Update streak
                user.update_streak(daily_stat.minutes_studied)
            
            return points_earned
        return 0

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenged_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    challenger_points = db.Column(db.Float, default=0.0)
    challenged_points = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, declined
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    points_gained = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    winner = db.relationship('User', foreign_keys=[winner_id], backref='challenges_won')
    
    def calculate_winner(self):
        if self.status == 'active' and datetime.utcnow() >= self.end_date:
            if self.challenger_points > self.challenged_points:
                self.winner_id = self.challenger_id
                self.points_gained = abs(self.challenger_points - self.challenged_points)
            elif self.challenged_points > self.challenger_points:
                self.winner_id = self.challenged_id
                self.points_gained = abs(self.challenged_points - self.challenger_points)
            # If tied, no winner
            
            self.status = 'completed'
            
            # Award challenge bonus points
            if self.winner_id:
                winner = db.session.get(User, self.winner_id)
                loser_id = self.challenged_id if self.winner_id == self.challenger_id else self.challenger_id
                loser = db.session.get(User, loser_id)
                
                if winner:
                    winner.total_points += self.points_gained
                    
                # Give consolation points to loser
                if loser:
                    loser.total_points += 2.0
                    
            # Send result emails
            try:
                from email_service import EmailService
                challenger = db.session.get(User, self.challenger_id)
                challenged = db.session.get(User, self.challenged_id)
                
                if challenger and getattr(challenger, 'challenge_emails', True):
                    is_challenger_winner = (self.winner_id == self.challenger_id) if self.winner_id else False
                    EmailService.send_challenge_result(challenger, self, is_challenger_winner)
                    
                if challenged and getattr(challenged, 'challenge_emails', True):
                    is_challenged_winner = (self.winner_id == self.challenged_id) if self.winner_id else False
                    EmailService.send_challenge_result(challenged, self, is_challenged_winner)
            except Exception as e:
                print(f"Failed to send challenge result emails: {e}")
                
            return True
        return False

class DailyStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    minutes_studied = db.Column(db.Integer, default=0)
    points_earned = db.Column(db.Float, default=0.0)
    tasks_completed = db.Column(db.Integer, default=0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)
