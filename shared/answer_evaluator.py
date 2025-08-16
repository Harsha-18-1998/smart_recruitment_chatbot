import os
import requests
import json
from dotenv import load_dotenv

# ---------------- Load API key ----------------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAIN_MODEL = "meta-llama/llama-3-70b-instruct"
FALLBACK_MODEL = MAIN_MODEL  # Using same model as fallback

# ---------------- LLM Call ----------------
def call_llm(model, prompt):
    """Call OpenRouter LLM and return text output."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4
    }
    try:
        resp = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=25)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return None
    except Exception:
        return None

# ---------------- Answer Evaluation ----------------
def evaluate_answer(question, answer):
    """
    Evaluate a candidate's answer using LLM.
    Returns a structured JSON:
    {
        "score": float 0-10,
        "strengths": ["bullet 1", "bullet 2", "bullet 3"],
        "suggestions": ["bullet 1", "bullet 2", "bullet 3"]
    }
    """

    # 1️⃣ Main evaluation prompt — request plain bullet points
    free_prompt = f"""
You are an expert interview evaluator.

Evaluate this answer in JSON format:

{{
  "score": number between 0 and 10,
  "strengths": ["short bullet point", "short bullet point", "short bullet point"],
  "suggestions": ["short bullet point", "short bullet point", "short bullet point"]
}}

Rules:
- Always provide 3 strengths and 3 suggestions (use 'N/A' if not applicable)
- Each point under 15 words
- Do NOT use 'Step 1' or numbering
- No paragraphs, only bullet points

Question: {question}

Answer: {answer}
"""
    main_output = call_llm(MAIN_MODEL, free_prompt)
    parsed = parse_llm_output(main_output)
    if parsed:
        return parsed

    # 2️⃣ Fallback prompt
    fallback_prompt = f"""
You are a professional interview evaluator.

Return output ONLY in JSON format:

{{
  "score": number between 0 and 10,
  "strengths": ["bullet 1", "bullet 2", "bullet 3"],
  "suggestions": ["bullet 1", "bullet 2", "bullet 3"]
}}

Rules:
- Each point must be concise, max 15 words
- Always provide 3 strengths and 3 suggestions (use 'N/A' if unknown)
- Do NOT include 'Step 1' or numbering
- No paragraphs

Question: {question}

Answer: {answer}
"""
    fallback_output = call_llm(FALLBACK_MODEL, fallback_prompt)
    parsed = parse_llm_output(fallback_output)
    if parsed:
        return parsed

    # 3️⃣ Final static fallback
    return {
        "score": 0,
        "strengths": ["Unable to evaluate", "N/A", "N/A"],
        "suggestions": ["Please try again", "N/A", "N/A"]
    }

# ---------------- Parse LLM Output ----------------
def parse_llm_output(output_text):
    """Try to parse LLM output into structured JSON with 3 bullets each."""
    if not output_text:
        return None
    try:
        parsed = json.loads(output_text)
        if (
            isinstance(parsed, dict)
            and "score" in parsed
            and "strengths" in parsed
            and "suggestions" in parsed
        ):
            # Ensure numeric score 0-10
            try:
                parsed["score"] = float(parsed.get("score", 0))
                parsed["score"] = max(0, min(10, parsed["score"]))
            except Exception:
                parsed["score"] = 0

            # Ensure strengths & suggestions are lists of 3 items
            strengths = [str(s).strip() for s in parsed.get("strengths", []) if s]
            suggestions = [str(s).strip() for s in parsed.get("suggestions", []) if s]

            while len(strengths) < 3:
                strengths.append("N/A")
            while len(suggestions) < 3:
                suggestions.append("N/A")

            parsed["strengths"] = strengths[:3]
            parsed["suggestions"] = suggestions[:3]

            return parsed
    except Exception:
        return None
