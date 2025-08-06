import os
import pandas as pd
from shared.llm_question_generator import generate_questions

def load_questions(role=None, subject=None):
    """
    Load interview questions either from local dataset or generate using LLM.
    - Tries to load from CSV files in the 'data' directory first.
    - If no local file found, falls back to generating via OpenRouter AI.
    """
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    topic = subject if subject else role
    if not topic:
        return []

    topic_cleaned = topic.lower().replace(" ", "_")  # e.g., "Data Analyst" → "data_analyst"
    file_name = f"{topic_cleaned}_questions.csv"
    file_path = os.path.join(base_dir, file_name)

    print("👉 Looking for question file at:", os.path.abspath(file_path))  # Debug print

    # Step 1: Try loading from CSV
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)

            if "Questions" in df.columns:
                questions = df["Questions"].dropna().tolist()
            else:
                questions = df.iloc[:, 0].dropna().tolist()

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
