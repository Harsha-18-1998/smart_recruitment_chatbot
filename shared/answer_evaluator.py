import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def evaluate_answer(question, answer):
    prompt = f"""
You are a mock interview evaluator.

Evaluate this answer.

Question: {question}

Answer: {answer}

Respond in JSON like:
{{
  "score": 8,
  "strengths": "Clearly explained, good structure.",
  "suggestions": "Add more technical depth and examples."
}}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "gpt-3.5-turbo",  # You can also try "gpt-4" if you prefer
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)

    if response.status_code == 200:
        try:
            content = response.json()['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            return {"score": 0, "strengths": "Error reading response.", "suggestions": str(e)}
    else:
        return {"score": 0, "strengths": "API Error", "suggestions": f"Status Code: {response.status_code}"}
