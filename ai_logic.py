import openai
import os

openai.api_key = os.getenv('OPENROUTER_API_KEY')

def process_message(message, user_id):
    if message in ['❤️', '👍', '🔥', '🙂']:
        message = "Клиент прислал emoji"

    system_prompt = (
        "Ты — ИИ-ассистент AI24Solutions. "
        "Ты ведешь клиента по воронке: интерес → прогрев → действие → дожим. "
        "Не философствуй, отвечай коротко, давай ссылки: https://ai24solutions.ru/#quiz"
    )

    response = openai.ChatCompletion.create(
        model="openrouter/gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    reply = response.choices[0].message['content']
    log_data = {'user_id': user_id, 'message': message, 'reply': reply}
    return reply, log_data
