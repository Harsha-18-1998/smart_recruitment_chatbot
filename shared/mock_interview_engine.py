import os
import pandas as pd
import random
import httpx
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def generate_questions(role=None, subject=None, num_questions=5):
    """
    Generate questions using OpenRouter LLM.
    Returns a list of unique, shuffled questions.
    """
    if not role and not subject:
        raise ValueError("Either role or subject must be provided.")

    topic = role if role else subject
    prompt = (
        f"Generate exactly {num_questions} mock interview questions for the topic: {topic}.\n"
        f"Return only a numbered list like:\n"
        f"1. What is...\n2. Explain...\nDo not include headings, titles, or any introductory text."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=data,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Step 1: Extract questions from numbered list
        questions = []
        seen = set()
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit():
                cleaned = line.lstrip("0123456789). ").strip()
                if cleaned.endswith("?") and cleaned not in seen:
                    questions.append(cleaned)
                    seen.add(cleaned)

        # Step 2: Fallback — catch lines ending with '?'
        if len(questions) < num_questions:
            for line in content.strip().split("\n"):
                line = line.strip()
                if line.endswith("?") and line not in seen:
                    questions.append(line)
                    seen.add(line)
                if len(questions) >= num_questions:
                    break

        # Step 3: Shuffle questions
        random.shuffle(questions)
        return questions[:num_questions]

    except Exception as e:
        print("Error calling OpenRouter API:", e)
        return []


def load_questions(role=None, subject=None):
    """
    Load interview questions either from local CSV or generate using LLM.
    - Tries to load from CSV files in 'data' directory first.
    - Falls back to AI-generated questions if CSV not found or empty.
    """
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    topic = subject if subject else role
    if not topic:
        return []

    topic_cleaned = topic.lower().replace(" ", "_")  # e.g., "Data Analyst" → "data_analyst"
    file_name = f"{topic_cleaned}_questions.csv"
    file_path = os.path.join(base_dir, file_name)

    print("👉 Looking for question file at:", os.path.abspath(file_path))

    # Step 1: Try loading from CSV
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if "Questions" in df.columns:
                questions = df["Questions"].dropna().tolist()
            else:
                questions = df.iloc[:, 0].dropna().tolist()

            questions = list(set(questions))  # Deduplicate local CSV questions
            random.shuffle(questions)         # Shuffle questions

            print(f"✅ Loaded {len(questions)} questions from: {file_name}")
            return questions
        except Exception as e:
            print(f"⚠️ Error reading local CSV: {e}")

    # Step 2: Fallback to LLM if CSV not found
    print(f"⚠️ No local file found, using AI to generate questions for: {topic}")
    questions = generate_questions(role=role, subject=subject, num_questions=5)
    if questions:
        print(f"✅ AI-generated {len(questions)} questions.")
    else:
        print("❌ AI failed to generate questions.")

    return questions
