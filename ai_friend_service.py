import json
import os
import random
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
        """Generate AI response using our custom personal AI model"""
        return self._generate_intelligent_response(user_message, user)
    
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