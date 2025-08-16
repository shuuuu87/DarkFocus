# Legacy utils.py - Email functionality moved to email_service.py
from email_service import EmailService

def send_verification_email(user):
    """Legacy wrapper for email verification"""
    return EmailService.send_verification_email(user)

def send_reset_email(user):
    """Legacy wrapper for password reset email"""
    return EmailService.send_reset_email(user)
