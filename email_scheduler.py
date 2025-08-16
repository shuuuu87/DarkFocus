from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz
import logging

class EmailScheduler:
    def send_super_motivation_emails(self):
        """Send super motivation emails to all users"""
        from app import db, app
        from models import User
        from email_service import EmailService
        with app.app_context():
            try:
                users = db.session.query(User).filter(
                    User.is_verified == True,
                    User.email_notifications == True
                ).all()
                count = 0
                for user in users:
                    if EmailService.send_super_motivation_email(user):
                        count += 1
                logging.info(f"Sent {count} super motivation emails")
            except Exception as e:
                logging.error(f"Error sending super motivation emails: {e}")
    """Background email scheduler for automated email campaigns"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Setup all scheduled email jobs"""
        
        # Daily reminder emails at 6 PM IST (18:00)
        self.scheduler.add_job(
            func=self.send_daily_reminders,
            trigger=CronTrigger(hour=18, minute=0, timezone=pytz.timezone('Asia/Kolkata')),
            id='daily_reminders',
            name='Send daily study reminders',
            replace_existing=True
        )

        # Streak warning emails at 9 PM IST (21:00)
        self.scheduler.add_job(
            func=self.send_streak_warnings,
            trigger=CronTrigger(hour=21, minute=0, timezone=pytz.timezone('Asia/Kolkata')),
            id='streak_warnings',
            name='Send streak warning emails',
            replace_existing=True
        )

        # Weekly progress emails every Sunday at 10 AM IST
        self.scheduler.add_job(
            func=self.send_weekly_progress,
            trigger=CronTrigger(day_of_week=6, hour=10, minute=0, timezone=pytz.timezone('Asia/Kolkata')),
            id='weekly_progress',
            name='Send weekly progress summaries',
            replace_existing=True
        )

        # Re-engagement emails every day at 12 PM IST
        self.scheduler.add_job(
            func=self.send_reengagement_emails,
            trigger=CronTrigger(hour=12, minute=0, timezone=pytz.timezone('Asia/Kolkata')),
            id='reengagement',
            name='Send re-engagement emails',
            replace_existing=True
        )

        # Welcome series emails every day at 9 AM IST
        self.scheduler.add_job(
            func=self.send_welcome_series,
            trigger=CronTrigger(hour=9, minute=0, timezone=pytz.timezone('Asia/Kolkata')),
            id='welcome_series',
            name='Send welcome series emails',
            replace_existing=True
        )

        # Super motivation emails every day at 12:30 PM IST
        self.scheduler.add_job(
            func=self.send_super_motivation_emails,
            trigger=CronTrigger(hour=12, minute=30, timezone=pytz.timezone('Asia/Kolkata')),
            id='super_motivation',
            name='Send super motivation emails',
            replace_existing=True
        )
    
    def start(self):
        """Start the email scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logging.info("Email scheduler started")
    
    def stop(self):
        """Stop the email scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("Email scheduler stopped")
    
    def send_daily_reminders(self):
        """Send daily study reminders to users who haven't studied today"""
        from app import db
        from models import User, DailyStats
        from email_service import EmailService
        from app import app
        
        with app.app_context():
            try:
                ist = pytz.timezone('Asia/Kolkata')
                today = datetime.now(ist).date()
                
                # Get users who haven't studied today and are active
                users_to_remind = db.session.query(User).filter(
                    User.is_verified.is_(True),
                    User.daily_reminders.is_(True)
                ).all()
                
                reminder_count = 0
                for user in users_to_remind:
                    # Check if user has studied today
                    daily_stat = DailyStats.query.filter_by(
                        user_id=user.id, 
                        date=today
                    ).first()
                    
                    if not daily_stat or daily_stat.minutes_studied == 0:
                        if EmailService.send_daily_reminder(user):
                            reminder_count += 1
                
                logging.info(f"Sent {reminder_count} daily reminder emails")
                
            except Exception as e:
                logging.error(f"Error sending daily reminders: {e}")
    
    def send_streak_warnings(self):
        """Send streak warning emails to users about to lose their streak"""
        from app import db
        from models import User, DailyStats
        from email_service import EmailService
        from app import app
        
        with app.app_context():
            try:
                ist = pytz.timezone('Asia/Kolkata')
                today = datetime.now(ist).date()
                
                # Get users with active streaks who haven't studied today
                users_at_risk = db.session.query(User).filter(
                    User.current_streak > 0,
                    User.is_verified.is_(True),
                    User.email_notifications.is_(True)
                ).all()
                
                warning_count = 0
                for user in users_at_risk:
                    # Check if user hasn't studied today
                    daily_stat = DailyStats.query.filter_by(
                        user_id=user.id, 
                        date=today
                    ).first()
                    
                    if not daily_stat or daily_stat.minutes_studied == 0:
                        if EmailService.send_streak_warning(user):
                            warning_count += 1
                
                logging.info(f"Sent {warning_count} streak warning emails")
                
            except Exception as e:
                logging.error(f"Error sending streak warnings: {e}")
    
    def send_weekly_progress(self):
        """Send weekly progress summaries"""
        from app import db
        from models import User, DailyStats
        from email_service import EmailService
        from app import app
        
        with app.app_context():
            try:
                # Get all active users
                active_users = db.session.query(User).filter(
                    User.is_verified.is_(True),
                    User.weekly_summaries.is_(True)
                ).all()
                
                progress_count = 0
                for user in active_users:
                    if EmailService.send_weekly_progress(user):
                        progress_count += 1
                
                logging.info(f"Sent {progress_count} weekly progress emails")
                
            except Exception as e:
                logging.error(f"Error sending weekly progress emails: {e}")
    
    def send_reengagement_emails(self):
        """Send re-engagement emails to inactive users"""
        from app import db
        from models import User, DailyStats
        from email_service import EmailService
        from app import app
        
        with app.app_context():
            try:
                ist = pytz.timezone('Asia/Kolkata')
                week_ago = datetime.now(ist).date() - timedelta(days=7)
                
                # Find users who haven't studied in the last 7 days
                inactive_users = db.session.query(User).filter(
                    User.is_verified.is_(True),
                    User.email_notifications.is_(True)
                ).all()
                
                reengagement_count = 0
                for user in inactive_users:
                    # Check if user has any recent activity
                    recent_stats = DailyStats.query.filter(
                        DailyStats.user_id == user.id,
                        DailyStats.date >= week_ago,
                        DailyStats.minutes_studied > 0
                    ).first()
                    
                    if not recent_stats:
                        if EmailService.send_reengagement_email(user):
                            reengagement_count += 1
                
                logging.info(f"Sent {reengagement_count} re-engagement emails")
                
            except Exception as e:
                logging.error(f"Error sending re-engagement emails: {e}")
    
    def send_welcome_series(self):
        """Send welcome series emails to new users"""
        from app import db
        from models import User, DailyStats
        from email_service import EmailService
        from app import app
        
        with app.app_context():
            try:
                today = datetime.utcnow().date()
                yesterday = today - timedelta(days=1)
                
                # Find users who registered yesterday (for day 1 email)
                new_users = db.session.query(User).filter(
                    User.joined_date >= yesterday,
                    User.joined_date < today,
                    User.is_verified.is_(True)
                ).all()
                
                welcome_count = 0
                for user in new_users:
                    if EmailService.send_welcome_series_day1(user):
                        welcome_count += 1
                
                logging.info(f"Sent {welcome_count} welcome series emails")
                
            except Exception as e:
                logging.error(f"Error sending welcome series emails: {e}")

# Global scheduler instance
email_scheduler = EmailScheduler()