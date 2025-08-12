import os
import httpx
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_questions(role=None, subject=None, num_questions=5):
    if not role and not subject:
        raise ValueError("Either role or subject must be provided.")

    topic = role if role else subject
    prompt = (
        f"Generate exactly {num_questions} mock interview questions for the topic: {topic}.\n"
        f"Return only a numbered list like:\n"
        f"1. What is...\n2. Explain...\nDo not include headings, titles, or any introductory or summary text."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:10000",  # Optional, but some models use this for logging
        "X-Title": "Smart Interview Bot",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Step 1: Try to extract questions from numbered list
        questions = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check if it starts with a number followed by dot or bracket
            if line[0].isdigit():
                cleaned = line.lstrip("0123456789). ").strip()
                if cleaned.endswith("?"):
                    questions.append(cleaned)

            if len(questions) >= num_questions:
                break

        # Step 2: Fallback — catch additional questions that end with '?'
        if len(questions) < num_questions:
            for line in content.strip().split("\n"):
                line = line.strip()
                if line.endswith("?") and line not in questions:
                    questions.append(line)
                if len(questions) >= num_questions:
                    break

        return questions[:num_questions]

    except Exception as e:
        print("Error calling OpenRouter API:", e)
        return []
