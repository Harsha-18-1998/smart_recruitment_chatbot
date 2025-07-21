from shared.db_config import get_db_connection
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

# ✅ Match resume to job descriptions using MySQL jobs table
def match_resume_to_jobs(skills):
    if not skills:
        return []

    resume_text = " ".join(skills)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT job_id, title, description FROM jobs")
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    if not jobs:
        return []

    job_texts = [f"{job['title']} {job['description']}" for job in jobs]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(job_texts + [resume_text])
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    top_indices = cosine_sim[0].argsort()[::-1][:3]

    matches = []
    for idx in top_indices:
        job = jobs[idx]
        matches.append({
            "title": job["title"],
            "description": job["description"],
            "score": round(cosine_sim[0][idx] * 100, 2)
        })

    return matches

# ✅ Chatbot reply logic using fuzzy title matching
def get_job_info_reply(user_message):
    user_message = user_message.lower()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT title, description FROM jobs")
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    best_match = None
    best_score = 0

    for job in jobs:
        score = fuzz.partial_ratio(user_message, job['title'].lower())
        if score > best_score:
            best_score = score
            best_match = job

    if best_score > 60:
        return f"{best_match['title']}: {best_match['description']}"

    if "list" in user_message and "job" in user_message:
        job_titles = [job['title'] for job in jobs]
        return "Here are the available jobs:\n- " + "\n- ".join(job_titles)

    if "skills" in user_message:
        # Optional: You can fetch this from database or keep a default list
        common_skills = ["Python", "SQL", "Java", "Machine Learning", "Communication", "Teamwork", "Leadership", "Cloud", "APIs", "Git"]
        return "Some common job-related skills:\n- " + "\n- ".join(common_skills[:10]) + "\n..."

    return "I'm here to help! Try asking about a job like 'backend dev' or say 'list jobs'."
