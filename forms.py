from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, EmailField, IntegerField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64, message="Username must be between 3 and 64 characters")
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match")
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64)
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message="Passwords must match")
    ])
    profile_image = FileField('Profile Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    def __init__(self, current_user, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.current_user = current_user
    
    def validate_username(self, username):
        if username.data != self.current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken.')
    
    def validate_email(self, email):
        if email.data != self.current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered.')

class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[
        DataRequired(), 
        Length(min=1, max=200, message="Title must be between 1 and 200 characters")
    ])
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=720, message="Duration must be between 1 and 720 minutes (12 hours)")
    ])

class ChallengeForm(FlaskForm):
    opponent_username = StringField('Opponent Username', validators=[
        DataRequired(), 
        Length(min=3, max=64)
    ])
    duration_days = SelectField('Duration', choices=[
        (2, '2 Days'),
        (7, '7 Days')
    ], coerce=int, validators=[DataRequired()])
    
    def validate_opponent_username(self, opponent_username):
        user = User.query.filter_by(username=opponent_username.data).first()
        if not user:
            raise ValidationError('User not found.')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match")
    ])
