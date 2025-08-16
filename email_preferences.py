"""Email preferences management for DARKSULFOCUS"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db

email_prefs = Blueprint('email_prefs', __name__)

@email_prefs.route('/email-preferences', methods=['GET', 'POST'])
@login_required
def manage_preferences():
    """Manage user email preferences"""
    if request.method == 'POST':
        # Update email preferences
        current_user.email_notifications = request.form.get('email_notifications') == 'on'
        current_user.daily_reminders = request.form.get('daily_reminders') == 'on'
        current_user.weekly_summaries = request.form.get('weekly_summaries') == 'on'
        current_user.achievement_emails = request.form.get('achievement_emails') == 'on'
        current_user.challenge_emails = request.form.get('challenge_emails') == 'on'
        
        db.session.commit()
        flash('Email preferences updated successfully!', 'success')
        return redirect(url_for('email_prefs.manage_preferences'))
    
    return render_template('email_preferences.html', user=current_user)

@email_prefs.route('/api/email-preferences', methods=['POST'])
@login_required
def api_update_preferences():
    """API endpoint for updating email preferences"""
    data = request.get_json()
    
    try:
        current_user.email_notifications = data.get('email_notifications', True)
        current_user.daily_reminders = data.get('daily_reminders', True)
        current_user.weekly_summaries = data.get('weekly_summaries', True)
        current_user.achievement_emails = data.get('achievement_emails', True)
        current_user.challenge_emails = data.get('challenge_emails', True)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Preferences updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400