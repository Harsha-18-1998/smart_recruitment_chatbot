import os
import requests
import json
from dotenv import load_dotenv

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
openai.api_key = OPENROUTER_API_KEY

PROMPT_TEMPLATE = """
You are an expert interviewer and evaluator.

Question: {question}

Candidate's answer: {answer}

Please provide an evaluation including:

1. A score from 0 to 10 based on relevance, accuracy, and completeness.
2. Specific strengths of the answer.
3. Clear suggestions on how to improve the answer.

Format your response strictly in the following JSON format:

{{
  "score": <number>,
  "strengths": "<detailed strengths>",
  "suggestions": "<actionable suggestions>"
}}

Do not add any other commentary or text.
"""

def evaluate_answer(question: str, answer: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(question=question, answer=answer)

    response = openai.ChatCompletion.create(
        model="meta-llama/llama-3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=250,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    text = response['choices'][0]['message']['content'].strip()

    # Extract JSON from response
    try:
        # Sometimes the model might add extra text — we use regex to extract JSON block
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            import json
            result = json.loads(json_match.group())
            return result
        else:
            return {
                "score": None,
                "strengths": "Failed to parse evaluation strengths.",
                "suggestions": "Failed to parse evaluation suggestions."
            }
    except Exception as e:
        return {
            "score": None,
            "strengths": f"Error parsing response: {str(e)}",
            "suggestions": "Could not generate suggestions due to parsing error."
        }