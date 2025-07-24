# shared/chatbot_engine.py

from shared.db_config import get_db_connection

def get_job_info_reply(user_msg: str) -> str:
    msg = user_msg.lower()

    # Simple intent mapping
    if any(kw in msg for kw in ["hi", "hello", "hey"]):
        return "Hello! I’m your recruitment assistant. How can I help you today?"

    elif "match" in msg and "job" in msg:
        return "Sure! Upload your resume to get matched with the most relevant jobs based on your skills."

    elif "apply" in msg:
        return "To apply for a job, just upload your resume and we’ll find the best matches for you."

    elif "job openings" in msg or "available jobs" in msg:
        return get_available_jobs()

    elif "bye" in msg:
        return "Goodbye! Let me know if you need any help later."

    return "I’m sorry, I didn’t understand that. You can ask me about job openings, resume upload, or how to apply!"

def get_available_jobs() -> str:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT title FROM job_posts LIMIT 5")  # Table name depends on your DB
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()

        if jobs:
            job_titles = "\n".join(f"- {job['title']}" for job in jobs)
            return f"Here are some current job openings:\n{job_titles}"
        else:
            return "There are no jobs listed at the moment."

    except Exception as e:
        return "Oops! Something went wrong while fetching job listings."
