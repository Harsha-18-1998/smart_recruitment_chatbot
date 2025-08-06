import os
import requests
from dotenv import load_dotenv
from shared.db_config import get_db_connection

# Load .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# -----------------------
# Rule-Based Responses
# -----------------------
def get_rule_based_reply(msg: str) -> str | None:
    msg = msg.lower().strip()

    greetings = ["hi", "hello", "hey"]
    # Match exact greetings or greetings as individual words (avoid partial matches)
    if any(kw == msg or kw in msg.split() for kw in greetings):
        return "Hello! I’m your recruitment assistant. How can I help you today?"

    if "match" in msg and "job" in msg:
        return "Sure! Upload your resume to get matched with the most relevant jobs based on your skills."

    if "apply" in msg:
        return "To apply for a job, just upload your resume and we’ll find the best matches for you."

    if "job openings" in msg or "available jobs" in msg:
        return get_available_jobs()

    if "bye" in msg or "goodbye" in msg:
        return "Goodbye! Let me know if you need any help later."

    return None  # unknown intent

def get_available_jobs() -> str:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT title FROM job_posts LIMIT 5")
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()

        if jobs:
            job_titles = "\n".join(f"- {job['title']}" for job in jobs)
            return f"Here are some current job openings:\n{job_titles}"
        else:
            return "There are no jobs listed at the moment."
    except:
        return "Oops! Something went wrong while fetching job listings."

# -----------------------
# Fallback to LLM
# -----------------------
def get_ai_reply(user_msg: str) -> str:
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("RENDER_EXTERNAL_URL", "https://your-app.onrender.com"),
                "X-Title": "SmartRecruitmentChatbot"
            },
            json={
                "model": "meta-llama/llama-3-70b-instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant for job seekers."},
                    {"role": "user", "content": user_msg}
                ]
            }
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"LLM Error: OpenRouter returned status {response.status_code}"

    except Exception as e:
        return f"Chatbot Error: {str(e)}"

# -----------------------
# Main Handler
# -----------------------
def get_job_info_reply(user_msg: str) -> str:
    rule_reply = get_rule_based_reply(user_msg)
    if rule_reply:
        return rule_reply
    else:
        return get_ai_reply(user_msg)
