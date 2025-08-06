# shared/llm_question_generator.py

import os
import httpx
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_questions(role=None, subject=None, num_questions=5):
    if not role and not subject:
        raise ValueError("Either role or subject must be provided.")

    topic = role if role else subject
    prompt = f"Generate {num_questions} mock interview questions for the topic: {topic}."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:10000",
        "X-Title": "Smart Interview Bot",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-3-70b-instruct",  
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse questions as separate lines
        questions = [line.strip("0123456789). ").strip() for line in content.strip().split("\n") if line.strip()]
        return questions[:num_questions]

    except Exception as e:
        print("Error calling OpenRouter API:", e)
        return []
