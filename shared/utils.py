from shared.db_config import get_db_connection

def get_latest_resume_data(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT name, email, skills, top_jobs, timestamp
        FROM resume_submissions
        WHERE email = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (email,))

    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data
