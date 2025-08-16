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
        system_prompt = (
            "Create a comprehensive study timetable in HTML table format with proper styling:\n"
            "- Include time slots, subjects, and break periods\n"
            "- Use colors and professional styling\n"
            "- Make it complete and visually appealing\n"
            "- Add icons and proper formatting"
        )
        max_tokens = 800  # Much higher for timetables
    elif is_detailed:
        system_prompt = (
            "You're a knowledgeable study buddy providing detailed explanations:\n"
            "- Give comprehensive, clear explanations\n"
            "- Break down complex topics step by step\n"
            "- Use examples to illustrate concepts\n"
            "- Be educational and thorough\n"
            "- Help the user truly understand the topic"
        )
        max_tokens = 800  # Higher for detailed explanations
    else:
        system_prompt = (
            "You are a friendly, knowledgeable AI study companion. Give clear, helpful, and complete answers to the user's questions:\n"
            "- Use a supportive and encouraging tone\n"
            "- Give explanations, examples, or advice as needed\n"
            "- Be concise but not overly brief (2-5 sentences is good)\n"
            "- If the user asks for a definition or explanation, provide a full answer\n"
            "- If the user just chats, respond naturally and keep the conversation going"
        )
        max_tokens = 200  # Allow more complete answers for regular responses

    if user_name:
        system_prompt += f"\nThe user's name is {user_name}."
    if ai_name:
        system_prompt += f"\nYour name is {ai_name}."
    if personality:
        system_prompt += f"\nYour personality is {personality}."

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_tokens": max_tokens,
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']
