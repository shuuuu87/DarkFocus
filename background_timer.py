"""
Background Timer Service
Handles server-side timer completion checking and auto-completion
"""
from datetime import datetime
import time
import threading
import logging
import pytz

class BackgroundTimerService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 60  # Check every 30 seconds
        
    def start(self):
        """Start the background timer service"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_checker, daemon=True)
            self.thread.start()
            logging.info("Background Timer Service started")
            
    def stop(self):
        """Stop the background timer service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logging.info("Background Timer Service stopped")
        
    def _run_checker(self):
        """Main loop to check for completed timers"""
        while self.running:
            try:
                # Check if we should run based on IST timezone
                if self._should_run_now():
                    # Import here to avoid circular imports
                    from app import app, db
                    with app.app_context():
                        self._check_completed_timers()
                        self._check_completed_challenges()
                        self._check_daily_streaks()
                else:
                    logging.info("Skipping background service - quiet hours (12 AM - 6 AM IST)")
            except Exception as e:
                logging.error(f"Error in background timer checker: {e}")
            
            # Wait before next check
            time.sleep(self.check_interval)
    
    def _should_run_now(self):
        """Check if background service should run (not between 12 AM - 6 AM IST)"""
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        current_hour = current_time.hour
        
        # Don't run between 12 AM (0) and 6 AM (6) IST
        if 0 <= current_hour < 6:
            return False
        return True
    
    def _check_completed_timers(self):
        """Check for timers that should be completed and process them"""
        from app import db
        from models import Task, Challenge
        
        # Find all active tasks that should be completed
        completed_tasks = Task.query.filter(
            Task.is_active.is_(True),
            Task.is_completed.is_(False),
            Task.expected_completion <= datetime.utcnow()
        ).all()
        
        if completed_tasks:
            logging.info(f"Found {len(completed_tasks)} completed timers")
            
        for task in completed_tasks:
            try:
                # Complete the task
                points_earned = task.complete_task()
                
                # Stop the server-side timer
                task.is_active = False
                task.started_at = None
                task.expected_completion = None
                
                db.session.commit()
                
                # Send achievement email if user has notifications enabled
                from models import User
                user = db.session.get(User, task.user_id)
                if user and user.achievement_emails:
                    try:
                        from email_service import EmailService
                        EmailService.send_achievement_unlock(user, 'task_completion', {
                            'task_title': task.title,
                            'points_earned': points_earned,
                            'total_points': user.total_points
                        })
                    except Exception as e:
                        logging.error(f"Failed to send completion email to user {user.id}: {e}")
                
                logging.info(f"Auto-completed task {task.id} for user {task.user_id}, awarded {points_earned:.1f} points")
                
            except Exception as e:
                logging.error(f"Error completing task {task.id}: {e}")
                db.session.rollback()
        

    
    def _check_completed_challenges(self):
        """Check for challenges that should be completed and process them"""
        from app import db
        from models import Challenge
        
        # Find all active challenges that should be completed
        completed_challenges = Challenge.query.filter(
            Challenge.status == 'active'
        ).filter(
            Challenge.end_date <= datetime.utcnow()
        ).all()
        
        if completed_challenges:
            logging.info(f"Found {len(completed_challenges)} completed challenges")
            
        for challenge in completed_challenges:
            try:
                challenge.calculate_winner()
                db.session.commit()
                logging.info(f"Challenge {challenge.id} completed automatically")
            except Exception as e:
                logging.error(f"Error completing challenge {challenge.id}: {e}")
                db.session.rollback()
    
    def _check_daily_streaks(self):
        """Check and update streaks for all users daily"""
        try:
            from models import User
            User.check_all_users_streaks()
            logging.info("Daily streak check completed for all users")
        except Exception as e:
            logging.error(f"Error checking daily streaks: {e}")

# Global instance
background_timer_service = BackgroundTimerService()