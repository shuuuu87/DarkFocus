import json
import os
import random
from mistral_api import call_mistral_api
from datetime import datetime, timedelta
from flask import current_app
from models import User, AIChatHistory, UserQuality, Task, DailyStats, db
from app import db as app_db
import re

class PersonalAIModel:
    """Custom AI model trained for personalized study assistance"""
    
    def __init__(self):
        # Core personality traits and knowledge base
        self.personalities = {
            'supportive': {
                'tone': 'encouraging and understanding',
                'responses': ['I believe in you!', 'You\'re doing great!', 'Every step counts!'],
                'approach': 'gentle and reassuring'
            },
            'motivational': {
                'tone': 'energetic and inspiring',
                'responses': ['Let\'s crush those goals!', 'You\'ve got this!', 'Push through!'],
                'approach': 'high-energy and goal-focused'
            },
            'casual': {
                'tone': 'friendly and relaxed',
                'responses': ['Hey there!', 'What\'s up?', 'Cool!'],
                'approach': 'informal and conversational'
            },
            'professional': {
                'tone': 'focused and structured',
                'responses': ['Let\'s analyze this systematically.', 'Based on your data...', 'I recommend...'],
                'approach': 'methodical and data-driven'
            }
        }
        
        # Study techniques database
        self.study_techniques = {
            'visual': ['mind maps', 'flashcards', 'diagrams', 'color coding'],
            'auditory': ['recording lectures', 'study groups', 'reading aloud', 'music'],
            'kinesthetic': ['hands-on practice', 'walking while studying', 'manipulatives'],
            'theoretical': ['concept mapping', 'analysis', 'connecting ideas'],
            'practical': ['real-world examples', 'case studies', 'applications']
        }
        
        # Motivational responses based on context
        self.motivation_bank = {
            'low_streak': [
                "Starting fresh is sometimes exactly what we need! Every expert was once a beginner.",
                "The best time to plant a tree was 20 years ago. The second best time is now!",
                "Small steps lead to big changes. Let's focus on just today."
            ],
            'high_streak': [
                "Your consistency is incredible! You're building amazing study habits.",
                "Look at that streak! You're proving to yourself what you're capable of.",
                "This momentum you've built is your superpower. Keep it going!"
            ],
            'rank_progress': [
                "Every point earned is progress toward your goals!",
                "You're climbing the ranks through dedication and hard work.",
                "Each study session is an investment in your future self."
            ]
        }

class AIFriendService:
    def get_ai_self_description(self):
        """Return a fixed self-description for the AI when asked about itself."""
        return (
            "I am a small AI who is always learning new things. My creator, trainer, and developer is the DarkSulFocus team (D.S.F team). "
            "I was created on August 15, 2025. I am designed to help users with their studies, motivation, and productivity. "
            "I can answer questions, help make study timetables, analyze your study habits, and even compete with other users. "
            "I remember your preferences and try to improve every day. My mission is to support and guide you to achieve your goals! "
            "If you want, you can even give me a special name.hope you have given."
        )
    def get_study_summary(self, user):
        """Generate a summary of the user's study habits and performance for AI analysis."""
        context = self.get_user_context(user)
        summary = (
            f"Study Summary for {context['name']}:\n"
            f"- Current streak: {context['current_streak']} days\n"
            f"- Max streak: {context['max_streak']} days\n"
            f"- Total study time: {context['total_study_time']} minutes\n"
            f"- Rank: {context['rank']}\n"
            f"- Total points: {context['total_points']}\n"
            f"- Recent study sessions: "
        )
        for stat in context.get('recent_study', []):
            summary += f"\n  {stat['date']}: {stat['minutes']} min, {stat['points']} pts, {stat['tasks']} tasks"
        if context.get('active_tasks'):
            summary += f"\n- Active tasks: " + ', '.join([t['name'] for t in context['active_tasks']])
        return summary
    def __init__(self):
        # Use our custom AI model instead of external APIs
        self.personal_ai = PersonalAIModel()
        self.ai_enabled = True  # Our custom AI is always available
    
    def get_user_context(self, user):
        """Get comprehensive user context for personalized responses"""
        context = {
            'name': user.username,
            'ai_name': user.ai_name,
            'personality': user.ai_personality,
            'rank': user.get_rank(),
            'total_points': user.total_points,
            'current_streak': user.current_streak,
            'max_streak': user.max_streak,
            'total_study_time': user.total_study_time,
            'joined_date': user.joined_date.strftime('%B %Y') if user.joined_date else 'Unknown'
        }
        
        # Get user qualities
        qualities = UserQuality.query.filter_by(user_id=user.id).all()
        context['qualities'] = {q.quality_name: q.quality_value for q in qualities}
        
        # Get recent study stats
        recent_stats = DailyStats.query.filter_by(user_id=user.id).filter(
            DailyStats.date >= datetime.now().date() - timedelta(days=7)
        ).order_by(DailyStats.date.desc()).limit(7).all()
        
        context['recent_study'] = []
        for stat in recent_stats:
            context['recent_study'].append({
                'date': stat.date.strftime('%Y-%m-%d'),
                'minutes': stat.minutes_studied,
                'points': stat.points_earned,
                'tasks': stat.tasks_completed
            })
        
        # Get recent incomplete tasks
        active_tasks = Task.query.filter_by(user_id=user.id, is_completed=False).all()
        context['active_tasks'] = [
            {'name': task.name, 'duration_minutes': task.duration_minutes}
            for task in active_tasks[:5]  # Limit to 5 recent tasks
        ]
        
        return context
    
    def extract_and_save_qualities(self, user_message, user):
        """Extract user qualities from message and save them"""
        # Simple keyword-based extraction
        quality_patterns = {
            'study_time_preference': r'(?:i (?:like|prefer|study|work) (?:to study |studying )?(?:in the |during the )?)(morning|afternoon|evening|night|early|late)',
            'favorite_subject': r'(?:i (?:like|love|enjoy|prefer) (?:studying |learning )?)(math|science|history|english|physics|chemistry|biology|literature|programming|coding|computer science|art|music)',
            'study_location': r'(?:i (?:study|work|prefer to study) (?:in|at) (?:the |my )?)(library|home|cafe|office|bedroom|desk|kitchen|outside)',
            'learning_style': r'(?:i (?:am|learn|study) (?:a |best with )?)(visual|auditory|kinesthetic|hands-on|practical|theoretical) (?:learner|person|student)?',
            'motivation': r'(?:i (?:am motivated by|get motivated by|need|want to|study for) )(grades|success|achievement|goals|career|future|family|personal growth)',
            'challenges': r'(?:i (?:struggle with|have trouble with|find it hard to|difficulty with) )(focus|concentration|procrastination|time management|motivation|math|reading|writing)'
        }
        
        message_lower = user_message.lower()
        extracted_qualities = []
        
        for quality_type, pattern in quality_patterns.items():
            matches = re.search(pattern, message_lower)
            if matches:
                quality_value = matches.group(1)
                
                # Check if this quality already exists
                existing_quality = UserQuality.query.filter_by(
                    user_id=user.id, quality_name=quality_type
                ).first()
                
                if existing_quality:
                    existing_quality.quality_value = quality_value
                    existing_quality.learned_date = datetime.utcnow()
                else:
                    new_quality = UserQuality(
                        user_id=user.id,
                        quality_name=quality_type,
                        quality_value=quality_value
                    )
                    db.session.add(new_quality)
                
                extracted_qualities.append((quality_type, quality_value))
        
        if extracted_qualities:
            db.session.commit()
        
        return extracted_qualities
    
    def generate_ai_response(self, user_message, user):
        """Generate AI response using Mistral 7B Instruct API with user study summary and AI self-description override."""
        context = self.get_user_context(user)
        study_summary = self.get_study_summary(user)
        
        # Check if user is asking about the AI itself
        about_ai_keywords = [
            'who are you', 'about you', 'yourself', 'what are you', 'who created you', 'who create you', 'who is your creator', 'who made you', 'who make you', 'your developer', 'your trainer', 'when were you created', 'your mission', 'your purpose', 'about yourself', 'your maker', 'your creator'
        ]
        user_message_lower = user_message.lower()
        if any(keyword in user_message_lower for keyword in about_ai_keywords):
            return self.get_ai_self_description()
        
        # Check if user is setting AI name
        name_patterns = [
            r'your name is (\w+)',
            r'call you (\w+)',
            r'i.*call you (\w+)',
            r'name you (\w+)',
            r'you.*name.*is (\w+)',
            r'call.*you.*(\w+)'
        ]
        
        import re
        from extensions import db
        for pattern in name_patterns:
            match = re.search(pattern, user_message_lower)
            if match:
                new_name = match.group(1).capitalize()
                if len(new_name) >= 2 and len(new_name) <= 20:  # Reasonable name length
                    user.ai_name = new_name
                    db.session.commit()
                    return f"Cool! I'm {new_name} now 😊"
        
        # Check if user is asking for a timetable/schedule - prioritize our custom function
        timetable_keywords = [
            'timetable', 'schedule', 'time table', 'study plan', 'routine', 'plan my day', 
            'study schedule', 'generate a timetable', 'create a schedule', 'generate timetable',
            'make a schedule', 'create timetable', 'study hrs', 'wake up at'
        ]
        if any(keyword in user_message_lower for keyword in timetable_keywords):
            return self.generate_timetable(user_message, user)

        # Get recent chat history for context
        recent_chats = self.get_chat_history(user, limit=4)
        conversation_context = ""
        
        # Build conversation context (skip the current user message since it's not saved yet)
        for chat in reversed(recent_chats):
            if chat.sender == 'user':
                conversation_context += f"User: {chat.message}\n"
            else:
                conversation_context += f"AI: {chat.message}\n"
        
        # For factual questions, provide minimal context
        factual_keywords = ['what is', 'define', 'explain', 'who is', 'tell me about']
        if any(user_message_lower.startswith(k) for k in factual_keywords):
            messages = [
                {"role": "user", "content": user_message}
            ]
        else:
            # Include conversation context for natural responses
            context_prompt = f"User info: {context.get('name')} (rank: {context.get('rank')}, streak: {context.get('current_streak')})\nRecent conversation:\n{conversation_context}\nCurrent message: {user_message}\n\nRespond naturally and contextually."
            messages = [
                {"role": "system", "content": context_prompt}
            ]
        
        # Check if this is a timetable request for longer response
        is_timetable_request = any(keyword in user_message.lower() for keyword in ['timetable', 'schedule', 'time table', 'study plan', 'routine'])
        
        # Check if user is asking for detailed explanation/doubt clarification
        detailed_explanation_keywords = [
            'explain in detail', 'detailed explanation', 'explain more', 'tell me more',
            'how does', 'why does', 'what is', 'define', 'concept', 'theory',
            'explain this', 'clarify', 'doubt', 'confused', 'don\'t understand',
            'help me understand', 'break it down', 'elaborate', 'in depth'
        ]
        is_detailed_request = any(keyword in user_message.lower() for keyword in detailed_explanation_keywords)
        
        ai_response = call_mistral_api(
            messages,
            user_name=context.get('name'),
            ai_name=context.get('ai_name'),
            personality=context.get('personality'),
            is_timetable=is_timetable_request,
            is_detailed=is_detailed_request
        )
        return ai_response
    
    def generate_timetable(self, user_message, user):
        """Generate a formatted timetable based on user request"""
        import re
        
        # Extract time range from message
        time_pattern = r'(\d{1,2})\s*(?:am|pm)?\s*(?:to|-)?\s*(\d{1,2})\s*(?:am|pm)?'
        wake_up_pattern = r'wake up at (\d{1,2})\s*(am|pm)?'
        hours_pattern = r'study (\d{1,2}) hrs'
        
        start_time = 9  # Default
        end_time = 17   # Default
        
        time_match = re.search(time_pattern, user_message.lower())
        wake_up_match = re.search(wake_up_pattern, user_message.lower())
        hours_match = re.search(hours_pattern, user_message.lower())
        
        if wake_up_match:
            start_time = int(wake_up_match.group(1))
            if wake_up_match.group(2) and wake_up_match.group(2) == 'pm' and start_time != 12:
                start_time += 12
            elif not wake_up_match.group(2) and start_time < 8:  # Assume PM if < 8 without AM/PM
                start_time += 12
        
        if hours_match:
            study_hours = int(hours_match.group(1))
            end_time = start_time + study_hours
        elif time_match:
            start_time = int(time_match.group(1))
            end_time = int(time_match.group(2))
        
        # Generate subjects (you can customize based on user preferences)
        subjects = ['Math', 'Science', 'English', 'History', 'Physics', 'Chemistry']
        
        # Create HTML table
        table_html = f"""
        <div style="margin: 15px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); color: black;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; text-align: center; font-weight: bold; font-size: 16px;">
        📅 Your Study Schedule ({start_time}:00 - {end_time}:00)
        </div>
        <table style="border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; color: black;">
        <thead>
        <tr style="background-color: #4CAF50; color: white;">
        <th style="border: none; padding: 12px; text-align: left; font-weight: 600; color: white;">⏰ Time</th>
        <th style="border: none; padding: 12px; text-align: left; font-weight: 600; color: white;">📖 Subject</th>
        <th style="border: none; padding: 12px; text-align: left; font-weight: 600; color: white;">⏱️ Duration</th>
        </tr>
        </thead>
        <tbody>
        """
        
        current_time = start_time
        subject_index = 0
        
        while current_time < end_time:
            # Determine if it's AM or PM
            if current_time < 12:
                time_str = f"{current_time}:00 AM"
                next_time_str = f"{current_time + 1}:00 AM" if current_time + 1 < 12 else "12:00 PM"
            elif current_time == 12:
                time_str = "12:00 PM"
                next_time_str = "1:00 PM"
            else:
                time_str = f"{current_time - 12}:00 PM"
                next_hour = current_time + 1
                next_time_str = f"{next_hour - 12}:00 PM" if next_hour > 12 else f"{next_hour}:00 PM"
            
            # Alternate between study and break every hour, but give 45 min study + 15 min break
            if (current_time - start_time) % 2 == 1:  # Every second hour is a break
                row_color = "#fff3cd"  # Light yellow for breaks
                subject = "🍎 Break"
                duration = "15 min"
            else:
                row_color = "#d4edda" if subject_index % 2 == 0 else "#f8f9fa"  # Alternate colors for subjects
                subject = f"📚 {subjects[subject_index % len(subjects)]}"
                duration = "45 min"
                subject_index += 1
            
            table_html += f"""
            <tr style="background-color: {row_color}; color: black;">
            <td style="border: 1px solid #ddd; padding: 8px; color: black !important;">{time_str} - {next_time_str}</td>
            <td style="border: 1px solid #ddd; padding: 8px; color: black !important;">{subject}</td>
            <td style="border: 1px solid #ddd; padding: 8px; color: black !important;">{duration}</td>
            </tr>
            """
            
            current_time += 1
        
        table_html += """
        </tbody>
        </table>
        <div style="background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 13px; color: black !important;">
        ✨ Your personalized study schedule! Feel free to adjust timing and subjects as needed.
        </div>
        </div>
        """
        
        return table_html
    
    def _generate_intelligent_response(self, user_message, user):
        """Generate intelligent response using our custom trained AI model"""
        context = self.get_user_context(user)
        message_lower = user_message.lower()
        personality = self.personal_ai.personalities.get(context['personality'], self.personal_ai.personalities['supportive'])
        
        # Analyze message intent and context
        intent = self._analyze_message_intent(message_lower, context)
        
        # Generate contextual response based on intent
        response = self._generate_contextual_response(intent, message_lower, context, personality)
        
        return response
    
    def _analyze_message_intent(self, message, context):
        """Analyze user message to understand intent and context"""
        intents = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
            'motivation': ['motivation', 'motivate', 'inspire', 'encourage', 'boost', 'pump up', 'feeling down', 'discouraged'],
            'study_help': ['study', 'learn', 'help', 'advice', 'technique', 'method', 'improve', 'better'],
            'schedule': ['schedule', 'plan', 'routine', 'timetable', 'organize', 'time management'],
            'progress': ['progress', 'rank', 'points', 'streak', 'achievement', 'goal'],
            'personal': ['about me', 'remember', 'know', 'quality', 'preference', 'like', 'dislike'],
            'settings': ['name', 'call you', 'change', 'personality'],
            'subject_help': ['math', 'science', 'history', 'english', 'physics', 'chemistry', 'programming', 'art'],
            'focus': ['focus', 'concentration', 'distracted', 'procrastinate', 'attention'],
            'stress': ['stress', 'anxious', 'worried', 'overwhelmed', 'pressure', 'tired']
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            if any(keyword in message for keyword in keywords):
                detected_intents.append(intent)
        
        return detected_intents[0] if detected_intents else 'general'
    
    def _generate_contextual_response(self, intent, message, context, personality):
        """Generate response based on analyzed intent and user context"""
        name = context['name']
        ai_name = context['ai_name']
        
        if intent == 'greeting':
            greetings = [
                f"Hello {name}! I'm {ai_name}, ready to help you achieve your study goals today!",
                f"Hey there, {name}! Great to see you. You're currently at {context['rank']} rank - impressive!",
                f"Hi {name}! Your {context['current_streak']}-day streak shows real dedication. What shall we work on?"
            ]
            return random.choice(greetings)
        
        elif intent == 'motivation':
            if context['current_streak'] == 0:
                return random.choice(self.personal_ai.motivation_bank['low_streak']) + f" You've studied {context['total_study_time']} minutes total - that's real commitment, {name}!"
            elif context['current_streak'] >= 7:
                return random.choice(self.personal_ai.motivation_bank['high_streak']) + f" {context['current_streak']} days straight - you're unstoppable, {name}!"
            else:
                return random.choice(self.personal_ai.motivation_bank['rank_progress']) + f" At {context['rank']} rank with {context['current_streak']} days streak, you're on fire!"
        
        elif intent == 'study_help':
            # Check user's known learning style
            learning_style = context['qualities'].get('learning_style', 'visual')
            techniques = self.personal_ai.study_techniques.get(learning_style, self.personal_ai.study_techniques['visual'])
            
            response = f"Based on what I know about you, {name}, I recommend these techniques: {', '.join(techniques[:2])}. "
            
            if context['active_tasks']:
                task_names = [task['name'] for task in context['active_tasks'][:2]]
                response += f"For your current tasks ({', '.join(task_names)}), try breaking them into 25-minute focused sessions."
            else:
                response += "Want to create a task to get started? I can help you plan the perfect study session!"
            
            return response
        
        elif intent == 'schedule':
            pref_time = context['qualities'].get('study_time_preference', 'morning')
            schedule_advice = {
                'morning': "Morning is perfect for tackling challenging subjects when your mind is fresh!",
                'afternoon': "Afternoon sessions work well for review and practice problems.",
                'evening': "Evening study is great for reviewing what you learned during the day.",
                'night': "Night study can be productive if you're naturally alert, just ensure good rest!"
            }
            
            return f"Great question, {name}! {schedule_advice.get(pref_time, schedule_advice['morning'])} I recommend 2-3 study blocks with breaks. Your {context['current_streak']}-day streak shows you know consistency!"
        
        elif intent == 'progress':
            rank = context['rank']
            points = context['total_points']
            streak = context['current_streak']
            
            return f"You're doing amazing, {name}! 🌟 Currently at {rank} rank with {points} points. Your {streak}-day streak shows real dedication. Each study session gets you closer to the next rank!"
        
        elif intent == 'settings':
            if 'call you' in message or 'name' in message:
                return f"I'm {ai_name} right now! Want to give me a new name? Just tell me what you'd like to call me and I'll remember it."
            return f"I'm {ai_name}, your {personality['tone']} study companion. You can change my name or personality anytime in settings!"
        
        elif intent == 'focus':
            focus_tips = [
                "Try the Pomodoro Technique: 25 minutes focused study, then 5-minute break.",
                "Remove distractions: phone in another room, close unnecessary tabs.",
                "Set a specific goal for each session: 'I will solve 5 math problems' works better than 'I will study math'."
            ]
            
            tip = random.choice(focus_tips)
            return f"Focus struggles are totally normal, {name}! Here's what works: {tip} Your {context['current_streak']}-day streak proves you can do this!"
        
        elif intent == 'stress':
            stress_support = [
                f"Take a deep breath, {name}. You've built a {context['current_streak']}-day streak - that shows real strength!",
                f"Feeling overwhelmed is normal, {name}. Let's break things down into smaller, manageable pieces.",
                f"Remember {name}, you've already proven your capability by reaching {context['rank']} rank. One step at a time!"
            ]
            return random.choice(stress_support) + " Want to talk about what's causing stress? I'm here to help."
        
        else:  # general response
            responses = [
                f"That's interesting, {name}! Tell me more - I love learning about your study journey.",
                f"I appreciate you sharing that with me, {name}. Your {context['rank']} rank shows you're dedicated to growth!",
                f"Thanks for telling me that, {name}! Every conversation helps me understand how to better support your {context['total_study_time']} minutes of study progress."
            ]
            return random.choice(responses)
    
    def _handle_name_change(self, message, user):
        """Handle AI name change requests"""
        # Extract potential name
        name_match = re.search(r'call you (\w+)', message.lower())
        if name_match:
            new_name = name_match.group(1).title()
            user.ai_name = new_name
            db.session.commit()
            return f"Perfect! You can call me {new_name} from now on. I love my new name, {user.username}!"
        return None
    
    def save_chat_message(self, user, sender, message):
        """Save chat message to database"""
        chat_entry = AIChatHistory(
            user_id=user.id,
            sender=sender,
            message=message
        )
        db.session.add(chat_entry)
        db.session.commit()
        return chat_entry
    
    def get_chat_history(self, user, limit=20):
        """Get recent chat history for a user"""
        return AIChatHistory.query.filter_by(user_id=user.id)\
            .order_by(AIChatHistory.timestamp.desc())\
            .limit(limit).all()
    
    def process_user_message(self, user, message):
        """Process a complete user message and return AI response"""
        # Save user message
        self.save_chat_message(user, 'user', message)
        
        # Extract and save any qualities mentioned
        self.extract_and_save_qualities(message, user)
        
        # Generate AI response
        ai_response = self.generate_ai_response(message, user)
        
        # Save AI response
        self.save_chat_message(user, 'ai', ai_response)
        
        return ai_response

# Global service instance
ai_friend_service = AIFriendService()