
from flask import url_for, current_app
from flask_mail import Message
from datetime import datetime, timedelta
import pytz
from models import DailyStats

class EmailService:

    @staticmethod
    def send_super_motivation_email(user):
        """Send a super motivation email to the user"""
        template = EmailService.get_email_template_base()
        msg = Message(
            'Super Motivation: You Can Do It! 💪',
            recipients=[user.email]
        )
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">Super Motivation</p>
            </div>
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Keep Going, You're Amazing!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    Remember, every small step you take brings you closer to your goals. Stay focused, stay positive, and never give up!<br><br>
                    <b>You have the power to achieve great things. Let's make today count!</b>
                </p>
            </div>
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    This is your daily boost from DARKSULFOCUS. You got this!
                </p>
            </div>
        </div>
        '''
        return EmailService._send_email(msg)
    """Comprehensive email service for DARKSULFOCUS"""
    
    @staticmethod
    def get_email_template_base():
        """Base template structure for all emails"""
        return {
            'header_style': "background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 30px; text-align: center;",
            'body_style': "background: #f8f9fa; padding: 30px;",
            'footer_style': "background: #1a1a1a; padding: 20px; text-align: center;",
            'button_style': "background: #00ff88; color: #1a1a1a; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;",
            'brand_color': "#00ff88",
            'text_color': "#666",
            'heading_color': "#333"
        }
    
    @staticmethod
    def send_verification_email(user):
        """Send email verification to user"""
        template = EmailService.get_email_template_base()
        token = user.verification_token
        
        msg = Message(
            'Verify Your DARKSULFOCUS Account',
            recipients=[user.email]
        )
        
        verify_url = url_for('main.verify_email', token=token, _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">Gamified Study Platform</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Welcome to DARKSULFOCUS!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    Thank you for joining our gamified study platform. To start your journey and access all features, 
                    please verify your email address by clicking the button below.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="{template['button_style']}">
                        Verify Email Address
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{verify_url}" style="color: {template['brand_color']};">{verify_url}</a>
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    If you didn't create this account, please ignore this email.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_reset_email(user):
        """Send password reset email to user"""
        template = EmailService.get_email_template_base()
        token = user.reset_token
        
        msg = Message(
            'Reset Your DARKSULFOCUS Password',
            recipients=[user.email]
        )
        
        reset_url = url_for('main.reset_password', token=token, _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">Password Reset Request</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Reset Your Password</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    We received a request to reset your password for your DARKSULFOCUS account. 
                    Click the button below to set a new password.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="{template['button_style']}">
                        Reset Password
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px;">
                    This link will expire in 1 hour. If the button doesn't work, copy and paste this link:<br>
                    <a href="{reset_url}" style="color: {template['brand_color']};">{reset_url}</a>
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    If you didn't request this reset, please ignore this email.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_daily_reminder(user):
        """Send daily study reminder if user hasn't studied today"""
        template = EmailService.get_email_template_base()
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).date()
        
        # Check if user has studied today
        daily_stat = DailyStats.query.filter_by(user_id=user.id, date=today).first()
        if daily_stat and daily_stat.minutes_studied > 0:
            return True  # User already studied today
        
        msg = Message(
            f'Your {user.current_streak}-day streak is waiting! 📚',
            recipients=[user.email]
        )
        
        dashboard_url = url_for('main.home', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">Daily Study Reminder</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Don't Break Your Streak!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    Hi {user.username}, you're on a <strong>{user.current_streak}-day study streak</strong>! 
                    Don't let it slip away - even a quick 15-minute study session can keep your momentum going.
                </p>
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: {template['brand_color']}; margin: 0 0 10px 0;">Your Stats:</h3>
                    <p style="margin: 5px 0; color: {template['text_color']};">🔥 Current Streak: {user.current_streak} days</p>
                    <p style="margin: 5px 0; color: {template['text_color']};">⭐ Total Points: {user.total_points:.1f}</p>
                    <p style="margin: 5px 0; color: {template['text_color']};">🏆 Rank: {user.get_rank()}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="{template['button_style']}">
                        Start Studying Now
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Quick tip: Start with a 25-minute Pomodoro session!
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    You can adjust your notification preferences in your profile settings.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_streak_warning(user):
        """Send warning when user is about to lose streak"""
        template = EmailService.get_email_template_base()
        
        msg = Message(
            f'🚨 Your {user.current_streak}-day streak expires today!',
            recipients=[user.email]
        )
        
        dashboard_url = url_for('main.home', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ff4444, #cc0000); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">⚠️ STREAK ALERT!</h1>
                <p style="color: #ffcccc; margin: 10px 0 0 0;">DARKSULFOCUS</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: #cc0000; margin-top: 0;">Don't Lose Your {user.current_streak}-Day Streak!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    <strong>{user.username}</strong>, your study streak expires at midnight today! You've worked hard for 
                    <strong>{user.current_streak} days</strong> - don't let it go to waste.
                </p>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #856404; margin: 0 0 10px 0;">Quick Study Ideas (10-30 minutes):</h3>
                    <ul style="color: #856404; margin: 0; padding-left: 20px;">
                        <li>Review flashcards or notes</li>
                        <li>Watch an educational video</li>
                        <li>Read one chapter or article</li>
                        <li>Practice problems or exercises</li>
                        <li>Plan tomorrow's study session</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: #ff4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Save My Streak!
                    </a>
                </div>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    This is an urgent reminder. Study at least 5 minutes before midnight to maintain your streak.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_weekly_progress(user):
        """Send weekly progress summary"""
        from app import db
        from models import DailyStats
        
        template = EmailService.get_email_template_base()
        ist = pytz.timezone('Asia/Kolkata')
        week_start = datetime.now(ist).date() - timedelta(days=7)
        week_end = datetime.now(ist).date()
        
        # Get weekly stats
        weekly_stats = db.session.query(DailyStats).filter(
            DailyStats.user_id == user.id,
            DailyStats.date >= week_start,
            DailyStats.date < week_end
        ).all()
        
        total_minutes = sum(stat.minutes_studied for stat in weekly_stats)
        total_points = sum(stat.points_earned for stat in weekly_stats)
        total_tasks = sum(stat.tasks_completed for stat in weekly_stats)
        study_days = len([stat for stat in weekly_stats if stat.minutes_studied > 0])
        
        msg = Message(
            f'Your Weekly Progress Summary - {total_minutes//60}h {total_minutes%60}m studied!',
            recipients=[user.email]
        )
        
        dashboard_url = url_for('main.progress', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">Weekly Progress Report</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Great Work This Week, {user.username}!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    Here's a summary of your study achievements from the past 7 days:
                </p>
                
                <div style="background: linear-gradient(135deg, #e8f5e8, #d4f1d4); padding: 25px; border-radius: 10px; margin: 20px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div style="text-align: center;">
                            <h3 style="color: {template['brand_color']}; margin: 0; font-size: 2em;">{total_minutes//60}h {total_minutes%60}m</h3>
                            <p style="margin: 5px 0; color: {template['text_color']};">Study Time</p>
                        </div>
                        <div style="text-align: center;">
                            <h3 style="color: {template['brand_color']}; margin: 0; font-size: 2em;">{total_points:.1f}</h3>
                            <p style="margin: 5px 0; color: {template['text_color']};">Points Earned</p>
                        </div>
                        <div style="text-align: center;">
                            <h3 style="color: {template['brand_color']}; margin: 0; font-size: 2em;">{total_tasks}</h3>
                            <p style="margin: 5px 0; color: {template['text_color']};">Tasks Completed</p>
                        </div>
                        <div style="text-align: center;">
                            <h3 style="color: {template['brand_color']}; margin: 0; font-size: 2em;">{study_days}/7</h3>
                            <p style="margin: 5px 0; color: {template['text_color']};">Study Days</p>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="{template['button_style']}">
                        View Detailed Progress
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Keep up the momentum! Consistency is the key to success.
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    Weekly reports are sent every Sunday. Manage your email preferences in settings.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_achievement_unlock(user, achievement_type, achievement_data):
        """Send achievement unlock notification"""
        template = EmailService.get_email_template_base()
        
        achievements = {
            'rank_up': {
                'title': f'Rank Up! You\'re now {achievement_data["new_rank"]}!',
                'message': f'Congratulations! You\'ve advanced from {achievement_data["old_rank"]} to {achievement_data["new_rank"]}!',
                'icon': '🏆'
            },
            'streak_milestone': {
                'title': f'{achievement_data["days"]}-Day Streak Achievement!',
                'message': f'Amazing! You\'ve maintained a {achievement_data["days"]}-day study streak!',
                'icon': '🔥'
            },
            'points_milestone': {
                'title': f'{achievement_data["points"]} Points Milestone!',
                'message': f'Incredible! You\'ve earned your {achievement_data["points"]}th point!',
                'icon': '⭐'
            },
            'hours_milestone': {
                'title': f'{achievement_data["hours"]} Hours Studied!',
                'message': f'Wow! You\'ve studied for {achievement_data["hours"]} total hours!',
                'icon': '📚'
            }
        }
        
        achievement = achievements.get(achievement_type, achievements['points_milestone'])
        
        msg = Message(
            f'{achievement["icon"]} {achievement["title"]}',
            recipients=[user.email]
        )
        
        dashboard_url = url_for('main.home', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ffd700, #ffed4e); padding: 30px; text-align: center;">
                <h1 style="color: #1a1a1a; margin: 0; font-size: 3em;">{achievement["icon"]}</h1>
                <h2 style="color: #1a1a1a; margin: 10px 0 0 0;">ACHIEVEMENT UNLOCKED!</h2>
                <p style="color: #333; margin: 5px 0 0 0;">DARKSULFOCUS</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0; text-align: center;">{achievement["title"]}</h2>
                <p style="color: {template['text_color']}; line-height: 1.6; text-align: center; font-size: 18px;">
                    {achievement["message"]}
                </p>
                
                <div style="background: linear-gradient(135deg, #fff9e6, #fff3b8); padding: 25px; border-radius: 10px; margin: 30px 0; text-align: center;">
                    <h3 style="color: #b8860b; margin: 0 0 15px 0;">Your Current Stats:</h3>
                    <p style="margin: 5px 0; color: #b8860b;">🏆 Rank: {user.get_rank()}</p>
                    <p style="margin: 5px 0; color: #b8860b;">⭐ Total Points: {user.total_points:.1f}</p>
                    <p style="margin: 5px 0; color: #b8860b;">🔥 Current Streak: {user.current_streak} days</p>
                    <p style="margin: 5px 0; color: #b8860b;">📚 Total Study Time: {user.total_study_time//60}h {user.total_study_time%60}m</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: #ffd700; color: #1a1a1a; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                        Continue Your Journey
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Keep pushing your limits! The next achievement is waiting for you.
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    Achievement notifications help you celebrate your progress. Manage preferences in settings.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_challenge_notification(challenged_user, challenger_user, challenge):
        """Send challenge notification"""
        template = EmailService.get_email_template_base()
        
        msg = Message(
            f'{challenger_user.username} challenged you to a study competition!',
            recipients=[challenged_user.email]
        )
        
        challenge_url = url_for('main.competition', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ff6b35, #ff8c42); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2.5em;">⚔️</h1>
                <h2 style="color: white; margin: 10px 0 0 0;">CHALLENGE RECEIVED!</h2>
                <p style="color: #ffe8e1; margin: 5px 0 0 0;">DARKSULFOCUS</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">You've Been Challenged!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    <strong>{challenger_user.username}</strong> has challenged you to a {challenge.duration_days}-day study competition! 
                    Are you ready to prove your dedication?
                </p>
                
                <div style="background: #f8f1ff; border: 2px solid #9c88ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #6c5ce7; margin: 0 0 15px 0;">Challenge Details:</h3>
                    <p style="margin: 5px 0; color: #6c5ce7;">⏱️ Duration: {challenge.duration_days} days</p>
                    <p style="margin: 5px 0; color: #6c5ce7;">🎯 Goal: Study more minutes than your opponent</p>
                    <p style="margin: 5px 0; color: #6c5ce7;">🏆 Winner takes all the glory!</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('main.accept_challenge', challenge_id=challenge.id, _external=True)}" style="background: #00cc6a; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px; margin: 0 10px;">
                        Accept Challenge
                    </a>
                    <a href="{url_for('main.decline_challenge', challenge_id=challenge.id, _external=True)}" style="background: #ff6b6b; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px; margin: 0 10px;">
                        Decline Challenge
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Don't keep them waiting! Accept or decline in your competition dashboard.
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    Challenge notifications keep the competition exciting. Manage preferences in settings.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_challenge_accepted(challenger_user, accepted_user, challenge):
        """Send challenge acceptance notification to challenger"""
        template = EmailService.get_email_template_base()
        
        msg = Message(
            f'{accepted_user.username} accepted your challenge!',
            recipients=[challenger_user.email]
        )
        
        dashboard_url = url_for('main.competition', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #00ff88, #00cc6a); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2.5em;">✅</h1>
                <h2 style="color: white; margin: 10px 0 0 0;">CHALLENGE ACCEPTED!</h2>
                <p style="color: #e8f5e8; margin: 5px 0 0 0;">DARKSULFOCUS</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">The Competition Begins!</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    Great news! <strong>{accepted_user.username}</strong> has accepted your {challenge.duration_days}-day challenge. 
                    The competition is now active!
                </p>
                
                <div style="background: #e8f5e8; border: 2px solid #00cc6a; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #00cc6a; margin: 0 0 15px 0;">Competition Details:</h3>
                    <p style="margin: 5px 0; color: #00cc6a;">⏰ Duration: {challenge.duration_days} days</p>
                    <p style="margin: 5px 0; color: #00cc6a;">🎯 Goal: Study more than your opponent</p>
                    <p style="margin: 5px 0; color: #00cc6a;">🚀 Status: Active - start studying!</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: #00cc6a; color: white; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                        View Competition
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    May the best studier win! Track your progress and see live results.
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    Good luck with your challenge! Competition makes us stronger.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_challenge_declined(challenger_user, declined_user, challenge):
        """Send challenge decline notification to challenger"""
        template = EmailService.get_email_template_base()
        
        msg = Message(
            f'{declined_user.username} declined your challenge',
            recipients=[challenger_user.email]
        )
        
        dashboard_url = url_for('main.competition', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #74b9ff, #0984e3); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2.5em;">❌</h1>
                <h2 style="color: white; margin: 10px 0 0 0;">CHALLENGE DECLINED</h2>
                <p style="color: #ddeeff; margin: 5px 0 0 0;">DARKSULFOCUS</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Challenge Not Accepted</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    <strong>{declined_user.username}</strong> has declined your {challenge.duration_days}-day challenge. 
                    Don't worry - there are many other competitors eager to test their skills!
                </p>
                
                <div style="background: #f0f7ff; border: 2px solid #74b9ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #0984e3; margin: 0 0 15px 0;">What's Next?</h3>
                    <p style="margin: 5px 0; color: #0984e3;">🎯 Challenge another user</p>
                    <p style="margin: 5px 0; color: #0984e3;">📚 Focus on your personal study goals</p>
                    <p style="margin: 5px 0; color: #0984e3;">🏆 Check the leaderboard for inspiration</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: #0984e3; color: white; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                        Find New Challenger
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Keep challenging yourself - that's how legends are made!
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    The competition never stops. Ready for your next challenge?
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_challenge_result(user, challenge, is_winner):
        """Send challenge result notification"""
        template = EmailService.get_email_template_base()
        
        if is_winner:
            subject = f'🏆 You won the challenge against {challenge.challenger.username if user.id == challenge.challenged_id else challenge.challenged.username}!'
            header_bg = "background: linear-gradient(135deg, #00ff88, #00cc6a);"
            result_text = "Congratulations! You won!"
            result_color = "#00cc6a"
        else:
            subject = f'Good fight! Challenge results with {challenge.challenger.username if user.id == challenge.challenged_id else challenge.challenged.username}'
            header_bg = "background: linear-gradient(135deg, #74b9ff, #0984e3);"
            result_text = "Great effort! Keep pushing!"
            result_color = "#0984e3"
        
        msg = Message(subject, recipients=[user.email])
        
        dashboard_url = url_for('main.competition', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{header_bg} padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2.5em;">{'🏆' if is_winner else '🤝'}</h1>
                <h2 style="color: white; margin: 10px 0 0 0;">CHALLENGE COMPLETE!</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">DARKSULFOCUS</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {result_color}; margin-top: 0; text-align: center;">{result_text}</h2>
                <p style="color: {template['text_color']}; line-height: 1.6; text-align: center;">
                    Your {challenge.duration_days}-day challenge has ended. Here are the final results:
                </p>
                
                <div style="background: #f8f9ff; border: 2px solid {result_color}; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: {result_color}; margin: 0 0 15px 0; text-align: center;">Final Scores:</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: center;">
                        <div>
                            <h4 style="margin: 0; color: {template['text_color']};">{challenge.challenger.username}</h4>
                            <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: {result_color};">{challenge.challenger_points:.1f} pts</p>
                        </div>
                        <div>
                            <h4 style="margin: 0; color: {template['text_color']};">{challenge.challenged.username}</h4>
                            <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: {result_color};">{challenge.challenged_points:.1f} pts</p>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: {result_color}; color: white; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        View Competition Dashboard
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    {'Ready for your next challenge?' if is_winner else 'Every challenge makes you stronger!'}
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    Competition drives excellence. Keep challenging yourself and others!
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_welcome_series_day1(user):
        """Send welcome series - Day 1: Getting started"""
        template = EmailService.get_email_template_base()
        
        msg = Message(
            'Welcome to DARKSULFOCUS! Your study journey begins now 🚀',
            recipients=[user.email]
        )
        
        dashboard_url = url_for('main.home', _external=True)
        help_url = url_for('main.help', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">Welcome Series - Day 1</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Welcome aboard, {user.username}! 🎉</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    You've just joined a community of focused learners who are serious about their study goals. 
                    Let's get you started on your journey to deep focus mastery!
                </p>
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: {template['brand_color']}; margin: 0 0 15px 0;">Quick Start Guide:</h3>
                    <ol style="color: {template['text_color']}; margin: 0; padding-left: 20px;">
                        <li style="margin: 10px 0;">Create your first study task</li>
                        <li style="margin: 10px 0;">Start the timer and focus deeply</li>
                        <li style="margin: 10px 0;">Earn points and build your streak</li>
                        <li style="margin: 10px 0;">Track your progress and rank up</li>
                    </ol>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="{template['button_style']}; margin: 0 10px 10px 0;">
                        Start Your First Task
                    </a>
                    <a href="{help_url}" style="background: transparent; color: {template['brand_color']}; border: 2px solid {template['brand_color']}; padding: 10px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Learn More
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Tomorrow: We'll show you how to set effective study goals!
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    This is part 1 of our 3-part welcome series to help you succeed.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def send_reengagement_email(user):
        """Send re-engagement email for inactive users"""
        template = EmailService.get_email_template_base()
        
        msg = Message(
            f'We miss you, {user.username}! Your study streak is waiting ❤️',
            recipients=[user.email]
        )
        
        dashboard_url = url_for('main.home', _external=True)
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="{template['header_style']}">
                <h1 style="color: {template['brand_color']}; margin: 0;">DARKSULFOCUS</h1>
                <p style="color: #cccccc; margin: 10px 0 0 0;">We Miss You!</p>
            </div>
            
            <div style="{template['body_style']}">
                <h2 style="color: {template['heading_color']}; margin-top: 0;">Come back, {user.username}! 👋</h2>
                <p style="color: {template['text_color']}; line-height: 1.6;">
                    It's been a while since your last study session, and we wanted to remind you that your 
                    goals are still waiting for you. Every expert was once a beginner who never gave up.
                </p>
                
                <div style="background: linear-gradient(135deg, #ffe8e8, #ffd6d6); padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #cc4444; margin: 0 0 15px 0;">Your Account Summary:</h3>
                    <p style="margin: 5px 0; color: #cc4444;">🏆 Rank: {user.get_rank()}</p>
                    <p style="margin: 5px 0; color: #cc4444;">⭐ Total Points: {user.total_points:.1f}</p>
                    <p style="margin: 5px 0; color: #cc4444;">📚 Total Study Time: {user.total_study_time//60}h {user.total_study_time%60}m</p>
                    <p style="margin: 5px 0; color: #cc4444;">💪 Ready to restart your streak!</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="{template['button_style']}">
                        Welcome Back - Start Studying
                    </a>
                </div>
                
                <p style="color: {template['text_color']}; font-size: 14px; text-align: center;">
                    Small steps lead to big achievements. Start with just 15 minutes today!
                </p>
            </div>
            
            <div style="{template['footer_style']}">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    We believe in your potential. Your future self will thank you for restarting today.
                </p>
            </div>
        </div>
        '''
        
        return EmailService._send_email(msg)

    @staticmethod
    def _send_email(msg):
        """Helper method to send email with error handling"""
        try:
            from app import mail
            mail.send(msg)
            current_app.logger.info(f'Email sent successfully to {msg.recipients}')
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to send email: {e}')
            return False