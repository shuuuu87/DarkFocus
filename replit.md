# DARKSULFOCUS - Gamified Study Platform

## Overview
DARKSULFOCUS is a gamified study platform built with Flask designed to encourage consistent study habits and track user progress. It leverages a point-based ranking system, streak tracking, and competitive challenges to motivate users. The platform aims to provide a comprehensive, engaging, and secure environment for users to manage their studies and connect with peers.

**Migration Status**: Successfully migrated from Replit Agent to Replit environment on August 15, 2025. All core features are operational including user authentication, AI Friend chat, study tracking, and gamification systems.

**Recent Updates (Aug 15, 2025)**:
- Fixed OpenRouter API key configuration for AI Friend functionality
- Implemented intelligent token system: 25 tokens for casual chat, 800 tokens for timetables and detailed explanations
- Enhanced AI conversation keyword matching to properly handle creator questions
- Made AI responses extremely natural and casual like texting a friend
- Added visual timetable generation: AI now creates beautiful HTML tables when users request study schedules
- Timetable feature includes gradient headers, alternating colors, emoji icons, and proper time formatting
- Fixed HTML rendering in chat history with | safe filter for persistent timetable display
- Added detailed explanation mode for educational queries with comprehensive responses
- All AI Friend features now fully functional with proper response patterns

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: PostgreSQL
- **Authentication**: Flask-Login with email verification and token-based password reset
- **Email**: Flask-Mail for transactional emails
- **File Handling**: Werkzeug for secure profile image uploads
- **Timer Storage**: Browser Local Storage (client-side persistence)
- **AI Model**: Custom-built Personal AI model for intent analysis, contextual responses, study technique recommendations, and motivational interactions. It features adaptive personalities and leverages user data for personalized guidance.

### Frontend Architecture
- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap 5 with a custom dark theme
- **JavaScript**: Vanilla JavaScript with Chart.js for data visualization
- **Responsive Design**: Mobile-first approach with sidebar navigation

### Application Structure
- **Blueprint-based routing**: For modular organization
- **Form handling**: WTForms for validation and CSRF protection
- **Architectural Pattern**: Traditional Model-View-Controller (MVC) pattern

### Core Features
- **User Management**: Comprehensive user registration, login, profile management, and session handling.
- **Gamification Engine**:
    - **Ranking System**: 8-tier system based on total study points.
    - **Points System**: Dynamic calculation based on study time and task completion.
    - **Streak Tracking**: Daily study streak with a limited grace day mechanism.
    - **Progress Visualization**: Charts and progress bars.
- **Task Management**: Creation of study tasks with time estimates, client-side timer system with persistence across sessions, and point rewards upon task completion.
- **Competition Features**: User challenges, leaderboards, and social elements for peer competition.
- **Email System**: Automated email notifications for verification, password reset, daily reminders, weekly summaries, achievements, and challenge updates.
- **Security**: CSRF protection, password hashing, email verification, token-based resets, and secure file uploads.

## External Dependencies

### Python Packages
- **Flask**: Core web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Flask-Mail**: Email functionality
- **WTForms**: Form handling and validation
- **Werkzeug**: WSGI utilities and security helpers
- **Pillow**: Image processing
- **pytz**: Timezone handling
- **APScheduler**: For email automation and scheduling

### Frontend Libraries
- **Bootstrap 5**: UI framework
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization

### Email Services
- **SMTP Configuration**: Configurable email provider (e.g., Gmail)