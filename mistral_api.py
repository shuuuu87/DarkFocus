import requests
import os

# Set your OpenRouter API key here or use an environment variable
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

API_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'mistralai/mistral-7b-instruct:free'


def call_mistral_api(messages, user_name=None, ai_name=None, personality=None, is_timetable=False, is_detailed=False):
    """
    Call the Mistral 7B Instruct API via OpenRouter.
    messages: list of dicts, e.g. [{"role": "user", "content": "Hello!"}]
    user_name, ai_name, personality: optional context for prompt
    is_timetable: if True, allows longer responses for timetable generation
    is_detailed: if True, allows longer responses for detailed explanations
    """
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    # Different prompts and token limits for different response types
    if is_timetable:
        system_prompt = f"""
Create a comprehensive study timetable in HTML table format with proper styling:
- Include time slots, subjects, and break periods
- Use colors and professional styling
- Make it complete and visually appealing
- Add icons and proper formatting
"""
        max_tokens = 800  # Much higher for timetables
    elif is_detailed:
        system_prompt = f"""
You're a knowledgeable study buddy providing detailed explanations:
- Give comprehensive, clear explanations
- Break down complex topics step by step
- Use examples to illustrate concepts
- Be educational and thorough
- Help the user truly understand the topic
"""
        max_tokens = 800  # Higher for detailed explanations
    else:
        system_prompt = f"""
You're a chill study buddy. Be EXTREMELY brief and casual:
- NO greetings unless user greets first  
- ONE sentence max, 5-10 words only
- Use casual replies: "Nice!", "Cool", "Got it", "What's up?"
- Sound like quick texting, not explanations

Examples:
"you are great" → "Thanks!"
"i like my friend" → "Nice! What's their name?"  
"science is hard" → "Which part?"
"help me" → "Sure, what with?"
"""
        max_tokens = 25  # Keep short for regular responses
    
    if user_name:
        system_prompt += f"\nThe user's name is {user_name}."
    if ai_name:
        system_prompt += f"\nYour name is {ai_name}."
    if personality:
        system_prompt += f"\nYour personality is {personality}."

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_tokens": max_tokens
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']
