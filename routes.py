import os
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy import desc
import logging
import pytz

from extensions import db, mail
from models import User, Task, Challenge, DailyStats, AIChatHistory, UserQuality
from forms import LoginForm, RegisterForm, ProfileForm, TaskForm, ChallengeForm, ForgotPasswordForm, ResetPasswordForm
from utils import send_verification_email, send_reset_email
from email_service import EmailService
from ai_friend_service import ai_friend_service

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return redirect(url_for('main.login'))

@main.route('/offline.html')
def offline():
    """Offline fallback page when app is used without internet"""
    return render_template('offline.html')

@main.route('/sw.js')
def service_worker():
    """Serve service worker from root for proper scope"""
    from flask import send_from_directory
    return send_from_directory('static/js', 'service-worker.js', mimetype='application/javascript')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username first, then by email
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if user.is_verified:
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.home'))
            else:
                flash('Please verify your email before logging in.', 'warning')
        else:
            flash('Invalid username/email or password', 'danger')
    
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.verification_token = secrets.token_urlsafe(32)
        user.is_verified = True  # Auto-verify for now due to email config issues
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Try to send verification email, but don't block registration if it fails
        try:
            send_verification_email(user)
            flash('Registration successful! Check your email for verification link.', 'success')
        except Exception as e:
            current_app.logger.error(f'Email send failed: {e}')
            flash('Registration successful! You can now log in directly.', 'success')
        
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Email verified successfully! You can now log in.', 'success')
    else:
        flash('Invalid verification token.', 'danger')
    
    return redirect(url_for('main.login'))

@main.route('/home')
@login_required
def home():
    # Get user's active tasks (not completed)
    active_tasks = Task.query.filter_by(user_id=current_user.id, is_completed=False).all()
    
    # Get today's study time for streak display
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    daily_stat = DailyStats.query.filter_by(user_id=current_user.id, date=today).first()
    today_minutes = daily_stat.minutes_studied if daily_stat else 0
    
    return render_template('home.html', 
                         active_tasks=active_tasks,
                         today_minutes=today_minutes,
                         user_rank=current_user.get_rank())

@main.route('/add_task', methods=['POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task()
        task.user_id = current_user.id
        task.title = form.title.data
        task.duration_minutes = form.duration_minutes.data
        db.session.add(task)
        db.session.commit()
        flash('Task added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    
    return redirect(url_for('main.home'))

# Timer control routes - now handled by JavaScript/Local Storage
@main.route('/start_timer/<int:task_id>')
@login_required
def start_timer(task_id):
    # Timer control is now handled by JavaScript local storage
    # This route exists for backward compatibility but redirects to home
    flash('Timer started! Control is now handled by your browser.', 'info')
    return redirect(url_for('main.home'))

@main.route('/pause_timer/<int:task_id>')
@login_required
def pause_timer(task_id):
    # Timer control is now handled by JavaScript local storage
    # This route exists for backward compatibility but redirects to home
    flash('Timer paused! Control is now handled by your browser.', 'info')
    return redirect(url_for('main.home'))

@main.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    
    return redirect(url_for('main.home'))

@main.route('/start_server_timer/<int:task_id>', methods=['POST'])
@login_required
def start_server_timer(task_id):
    """Start a task timer on the server side"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_completed=False).first()
    
    if task:
        # Pause all other active timers for this user (only one timer at a time)
        Task.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
        
        # Start this timer
        task.start_timer()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Timer started',
            'expected_completion': task.expected_completion.isoformat(),
            'remaining_seconds': task.get_remaining_seconds()
        })
    
    return jsonify({'success': False, 'error': 'Task not found'})

@main.route('/pause_server_timer/<int:task_id>', methods=['POST'])
@login_required
def pause_server_timer(task_id):
    """Pause a task timer"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_completed=False).first()
    
    if task:
        task.pause_timer()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Timer paused',
            'remaining_seconds': task.get_remaining_seconds()
        })
    
    return jsonify({'success': False, 'error': 'Task not found'})

@main.route('/get_timer_status/<int:task_id>', methods=['GET'])
@login_required
def get_timer_status(task_id):
    """Get current timer status"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'})
    
    # If task is already completed, return completed status
    if task.is_completed:
        return jsonify({
            'success': True,
            'completed': True,
            'points_earned': 0,  # Points already awarded
            'message': 'Task already completed!'
        })
    
    # Check if timer should be completed
    if task.is_timer_completed():
        # Auto-complete the task
        points_earned = task.complete_task()
        task.is_active = False
        task.started_at = None
        task.expected_completion = None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'completed': True,
            'points_earned': points_earned,
            'message': 'Task completed!'
        })
    
    return jsonify({
        'success': True,
        'is_active': task.is_active,
        'is_completed': task.is_completed,
        'remaining_seconds': task.get_remaining_seconds()
    })

@main.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task_route(task_id):
    """Complete a task - called when timer reaches zero"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_completed=False).first()
    
    if task:
        # Store old values for achievement checking
        old_rank = current_user.get_rank()
        old_points = current_user.total_points
        old_streak = current_user.current_streak
        old_hours = current_user.total_study_time // 60
        
        # Stop server-side timer and complete task
        task.is_active = False
        task.started_at = None
        task.expected_completion = None
        points_earned = task.complete_task()
        db.session.commit()
        
        # Check for achievements and send emails if enabled
        if current_user.achievement_emails:
            # Check for rank up
            new_rank = current_user.get_rank()
            if old_rank != new_rank:
                EmailService.send_achievement_unlock(current_user, 'rank_up', {
                    'old_rank': old_rank,
                    'new_rank': new_rank
                })
            
            # Check for points milestones (every 100 points)
            if (int(old_points) // 100) < (int(current_user.total_points) // 100):
                milestone = (int(current_user.total_points) // 100) * 100
                EmailService.send_achievement_unlock(current_user, 'points_milestone', {
                    'points': milestone
                })
            
            # Check for streak milestones
            if current_user.current_streak != old_streak and current_user.current_streak in [7, 30, 100, 365]:
                EmailService.send_achievement_unlock(current_user, 'streak_milestone', {
                    'days': current_user.current_streak
                })
            
            # Check for hours milestones (every 10 hours)
            new_hours = current_user.total_study_time // 60
            if (old_hours // 10) < (new_hours // 10):
                milestone_hours = (new_hours // 10) * 10
                EmailService.send_achievement_unlock(current_user, 'hours_milestone', {
                    'hours': milestone_hours
                })
        
        return jsonify({
            'success': True, 
            'completed': True, 
            'points_earned': points_earned,
            'message': f'Task completed! You earned {points_earned:.1f} points.'
        })
    
    return jsonify({'error': 'Task not found or already completed'})

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(current_user)
    
    if form.validate_on_submit():
        # Check current password if trying to change password
        if form.new_password.data:
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('profile.html', form=form)
            current_user.set_password(form.new_password.data)
        
        # Handle profile image upload
        if form.profile_image.data:
            try:
                file = form.profile_image.data
                filename = secure_filename(file.filename)
                
                # Generate unique filename
                unique_filename = f"{current_user.id}_{secrets.token_hex(8)}_{filename}"
                
                # Save file
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, unique_filename)
                
                # Resize and save image
                image = Image.open(file)
                image = image.convert('RGB')  # Convert to RGB if needed
                
                # Resize to 300x300 pixels
                image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                image.save(file_path, 'JPEG', quality=85)
                
                # Delete old profile image if it exists and isn't default
                if current_user.profile_image and current_user.profile_image != 'default.png':
                    old_file_path = os.path.join(upload_path, current_user.profile_image)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                current_user.profile_image = unique_filename
                flash('Profile image updated successfully!', 'success')
            except Exception as e:
                flash('Error uploading image. Please try again.', 'danger')
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    # Pre-populate form
    form.username.data = current_user.username
    form.email.data = current_user.email
    
    return render_template('profile.html', form=form)

@main.route('/progress')
@login_required
def progress():
    # Get last 30 days of study data
    ist = pytz.timezone('Asia/Kolkata')
    end_date = datetime.now(ist).date()
    start_date = end_date - timedelta(days=29)
    
    daily_stats = DailyStats.query.filter_by(user_id=current_user.id).filter(
        DailyStats.date >= start_date,
        DailyStats.date <= end_date
    ).all()
    
    # Create data for chart
    chart_data = []
    current_date = start_date
    stats_dict = {stat.date: stat.minutes_studied for stat in daily_stats}
    
    while current_date <= end_date:
        minutes = stats_dict.get(current_date, 0)
        hours = minutes / 60.0
        chart_data.append({
            'date': current_date.strftime('%b %d'),
            'hours': round(hours, 1)
        })
        current_date += timedelta(days=1)
    
    return render_template('progress.html', chart_data=chart_data)

@main.route('/competition', methods=['GET', 'POST'])
@login_required
def competition():
    form = ChallengeForm()
    
    if form.validate_on_submit():
        opponent = User.query.filter_by(username=form.opponent_username.data).first()
        
        if opponent and opponent.id == current_user.id:
            flash('You cannot challenge yourself!', 'danger')
        elif opponent:
            challenge = Challenge()
            challenge.challenger_id = current_user.id
            challenge.challenged_id = opponent.id
            challenge.duration_days = form.duration_days.data
            challenge.end_date = datetime.utcnow() + timedelta(days=form.duration_days.data)
            challenge.status = 'pending'  # Should start as pending, not active
            db.session.add(challenge)
            db.session.commit()
            
            # Send challenge notification email (check if user has challenge emails enabled)
            try:
                # Use hasattr to check if challenge_emails field exists, default to True if not
                if getattr(opponent, 'challenge_emails', True):
                    from email_service import EmailService
                    EmailService.send_challenge_notification(opponent, current_user, challenge)
                    print(f"Challenge email sent to {opponent.username}")
                else:
                    print(f"Challenge emails disabled for {opponent.username}")
            except Exception as e:
                print(f"Failed to send challenge email: {e}")
            
            flash(f'Challenge sent to {opponent.username}!', 'success')
            return redirect(url_for('main.competition'))
        else:
            flash('User not found!', 'danger')
    
    # Get user's challenges
    sent_challenges = Challenge.query.filter_by(challenger_id=current_user.id).order_by(Challenge.created_at.desc()).limit(10).all()
    received_challenges = Challenge.query.filter_by(challenged_id=current_user.id).order_by(Challenge.created_at.desc()).limit(10).all()
    
    # Get active challenges to show current progress
    active_challenges = Challenge.query.filter_by(status='active').filter(
        (Challenge.challenger_id == current_user.id) | (Challenge.challenged_id == current_user.id)
    ).all()
    
    return render_template('competition.html', 
                         form=form,
                         sent_challenges=sent_challenges,
                         received_challenges=received_challenges,
                         active_challenges=active_challenges)

@main.route('/accept_challenge/<int:challenge_id>')
@login_required
def accept_challenge(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id, challenged_id=current_user.id).first_or_404()
    challenge.status = 'active'
    challenge.start_date = datetime.utcnow()  # Reset start date when accepted
    challenge.end_date = datetime.utcnow() + timedelta(days=challenge.duration_days)
    db.session.commit()
    
    # Send acceptance confirmation email to challenger 
    challenger = User.query.get(challenge.challenger_id)
    if challenger:
        try:
            # Use hasattr to check if challenge_emails field exists, default to True if not
            if getattr(challenger, 'challenge_emails', True):
                from email_service import EmailService
                EmailService.send_challenge_accepted(challenger, current_user, challenge)
                print(f"Challenge acceptance email sent to {challenger.username}")
            else:
                print(f"Challenge emails disabled for {challenger.username}")
        except Exception as e:
            print(f"Failed to send challenge acceptance email: {e}")
    
    flash('Challenge accepted!', 'success')
    return redirect(url_for('main.competition'))

@main.route('/decline_challenge/<int:challenge_id>')
@login_required
def decline_challenge(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id, challenged_id=current_user.id).first_or_404()
    challenge.status = 'declined'
    db.session.commit()
    
    # Send decline notification email to challenger if they have challenge emails enabled
    challenger = User.query.get(challenge.challenger_id)
    if challenger:
        try:
            if getattr(challenger, 'challenge_emails', True):
                from email_service import EmailService
                EmailService.send_challenge_declined(challenger, current_user, challenge)
                print(f"Challenge decline email sent to {challenger.username}")
            else:
                print(f"Challenge emails disabled for {challenger.username}")
        except Exception as e:
            print(f"Failed to send challenge decline email: {e}")
    
    flash('Challenge declined.', 'info')
    return redirect(url_for('main.competition'))

@main.route('/leaderboard')
@login_required
def leaderboard():
    # Get top 10 users by total points
    top_users = User.query.order_by(User.total_points.desc()).limit(10).all()
    
    leaderboard_data = []
    ist = pytz.timezone('Asia/Kolkata')
    for i, user in enumerate(top_users, 1):
        # Calculate last active (last completed task or task creation)
        last_completed_task = Task.query.filter_by(user_id=user.id, is_completed=True).order_by(Task.completed_at.desc()).first()
        last_any_task = Task.query.filter_by(user_id=user.id).order_by(Task.created_at.desc()).first()

        if last_completed_task and last_completed_task.completed_at:
            last_active_utc = last_completed_task.completed_at
        elif last_any_task:
            last_active_utc = last_any_task.created_at
        else:
            last_active_utc = user.joined_date

        # Convert UTC to Asia/Kolkata
        if last_active_utc and last_active_utc.tzinfo is None:
            last_active_utc = last_active_utc.replace(tzinfo=pytz.utc)
        last_active = last_active_utc.astimezone(ist) if last_active_utc else None

        leaderboard_data.append({
            'rank': i,
            'user': user,
            'points': user.total_points,
            'rank_name': user.get_rank(),
            'streak': user.current_streak,
            'last_active': last_active
        })
    
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)

@main.route('/help')
def help():
    return render_template('help.html')

@main.route('/test-email')
@login_required
def test_email():
    """Test email functionality (development only)"""
    if current_user.achievement_emails:
        EmailService.send_achievement_unlock(current_user, 'rank_up', {
            'old_rank': 'Initiate',
            'new_rank': 'Grinder'
        })
        flash('Test achievement email sent!', 'success')
    else:
        flash('Achievement emails are disabled in your preferences.', 'info')
    return redirect(url_for('main.home'))

@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user.reset_token = secrets.token_urlsafe(32)
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            send_reset_email(user)
        
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('main.login'))
    
    return render_template('forgot_password.html', form=form)

@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expires < datetime.utcnow():
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('main.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

def save_profile_image(form_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)
    
    # Resize image
    output_size = (150, 150)
    img = Image.open(form_image)
    img.thumbnail(output_size)
    img.save(picture_path)
    
    return picture_fn

@main.route('/ai-friend')
@login_required
def ai_friend():
    """AI Friend chat page"""
    # Get recent chat history
    chat_history = ai_friend_service.get_chat_history(current_user, limit=20)
    chat_history.reverse()  # Show oldest first
    
    # Get user qualities for display
    user_qualities = UserQuality.query.filter_by(user_id=current_user.id).all()
    
    return render_template('ai_friend.html', 
                         chat_history=chat_history,
                         user_qualities=user_qualities,
                         ai_enabled=ai_friend_service.ai_enabled)

@main.route('/ai-friend/chat', methods=['POST'])
@login_required
def ai_friend_chat():
    """Process AI Friend chat message"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Process the message and get AI response
        ai_response = ai_friend_service.process_user_message(current_user, user_message)
        
        return jsonify({
            'success': True,
            'ai_response': ai_response,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        current_app.logger.error(f"AI Friend chat error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

@main.route('/ai-friend/settings', methods=['POST'])
@login_required
def ai_friend_settings():
    """Update AI Friend settings"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Update AI name
        if 'ai_name' in data:
            new_name = data['ai_name'].strip()[:64]
            if new_name:
                current_user.ai_name = new_name
        
        # Update personality
        if 'ai_personality' in data:
            personality = data['ai_personality']
            if personality in ['supportive', 'motivational', 'casual', 'professional']:
                current_user.ai_personality = personality
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    
    except Exception as e:
        current_app.logger.error(f"Settings update error: {e}")
        return jsonify({'error': 'Failed to update settings'}), 500

@main.route('/ai-friend/clear-history', methods=['POST'])
@login_required
def clear_ai_history():
    """Clear AI chat history"""
    try:
        AIChatHistory.query.filter_by(user_id=current_user.id).delete()
        UserQuality.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chat history and learned qualities cleared'})
    
    except Exception as e:
        current_app.logger.error(f"Clear history error: {e}")
        return jsonify({'error': 'Failed to clear history'}), 500
