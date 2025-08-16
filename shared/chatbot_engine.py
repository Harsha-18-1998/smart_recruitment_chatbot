import os
import requests
from dotenv import load_dotenv
from shared.db_config import get_db_connection
from rapidfuzz import fuzz

# Load .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# -----------------------
# Rule-Based Responses with Semantic Matching
# -----------------------
def get_rule_based_reply(msg: str, history: list = None) -> str | None:
    msg_clean = msg.lower().strip()
    greetings = ["hi", "hello", "hey"]
    
    # Exact or fuzzy greetings
    if any(fuzz.partial_ratio(msg_clean, kw) > 80 for kw in greetings):
        return "Hello! I’m your recruitment assistant. How can I help you today?"

    if "match" in msg_clean and "job" in msg_clean:
        return "Sure! Upload your resume to get matched with the most relevant jobs based on your skills."

    if "apply" in msg_clean:
        return "To apply for a job, just upload your resume and we’ll find the best matches for you."

    if "job openings" in msg_clean or "available jobs" in msg_clean:
        return get_available_jobs()

    if "prepare" in msg_clean or "data scientist" in msg_clean:
        # Could trigger a structured career advice reply
        return "I can help you prepare for Data Scientist roles. Would you like a **full roadmap** or a **quick checklist**?"

    if "bye" in msg_clean or "goodbye" in msg_clean:
        return "Goodbye! Let me know if you need any help later."

    return None  # Unknown intent

# -----------------------
# Job Search Integration
# -----------------------
def get_available_jobs(query: str = None) -> str:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if query:
            # Semantic search placeholder (could use embeddings later)
            cursor.execute("SELECT title FROM job_posts WHERE title LIKE %s LIMIT 5", (f"%{query}%",))
        else:
            cursor.execute("SELECT title FROM job_posts LIMIT 5")
            
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()

        if jobs:
            job_titles = "\n".join(f"- {job['title']}" for job in jobs)
            return f"Here are some current job openings:\n{job_titles}"
        else:
            return "There are no jobs listed at the moment."
    except Exception as e:
        return f"Oops! Something went wrong while fetching job listings. ({str(e)})"

# -----------------------
# AI-Based Responses (Context-Aware)
# -----------------------
def get_ai_reply(user_msg: str, history: list = None) -> str:
    try:
        messages = [{"role": "system", "content": "You are a helpful assistant for job seekers."}]
        if history:
            # Append previous conversation for context
            messages.extend(history)
        messages.append({"role": "user", "content": user_msg})

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
                "messages": messages
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
def get_job_info_reply(user_msg: str, history: list = None) -> str:
    """
    Returns a chatbot reply based on rule-based first, then AI fallback.
    History is a list of previous messages to provide context.
    """
    rule_reply = get_rule_based_reply(user_msg, history)
    if rule_reply:
        return rule_reply
    else:
        return get_ai_reply(user_msg, history)
