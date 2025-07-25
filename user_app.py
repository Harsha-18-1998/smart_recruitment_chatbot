import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from shared.resume_parser import extract_skills
from shared.job_matcher import match_resume_to_jobs
from shared.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "defaultsecret")

# Flask App Setup
app = Flask(__name__, template_folder='user_templates')
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

# Use eventlet for production (Render needs async support)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            conn.commit()
            flash("Signup successful. Please login.")
            return redirect(url_for('login'))
        except:
            flash("Username already exists.")
            return redirect(url_for('signup'))
        finally:
            cursor.close()
            conn.close()
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            flash("Login successful.")
            return redirect(url_for('upload_resume_form'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out.")
    return redirect(url_for('login'))


@app.route('/dashboard')
def user_dashboard():
    if 'user' not in session:
        flash("Login required.")
        return redirect(url_for('login'))

    user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, email, skills, top_jobs, timestamp
        FROM resume_submissions
        WHERE email = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (user,))
    latest = cursor.fetchone()
    cursor.close()
    conn.close()

    if not latest:
        flash("Please upload your resume.")
        return redirect(url_for('upload_resume_form'))

    return render_template('user_dashboard.html', data=latest)


@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume_form():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        file = request.files['resume']

        if not file:
            flash("Please upload a valid resume file.")
            return redirect(url_for('user_dashboard'))

        resume_text = file.read().decode('utf-8')
        skills = extract_skills(resume_text)
        matches = match_resume_to_jobs(skills)

        top_jobs = "; ".join([job['title'] for job in matches])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resume_submissions (name, email, skills, top_jobs, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, ", ".join(skills), top_jobs, timestamp))
        conn.commit()
        cursor.close()
        conn.close()

        data = {
            'name': name,
            'email': email,
            'skills': ", ".join(skills),
            'top_jobs': top_jobs,
            'timestamp': timestamp
        }

        flash("Resume uploaded and processed successfully.")
        return render_template('user_dashboard.html', data=data)

    return render_template('upload_resume.html')


# WebSocket Chatbot Handler
@socketio.on('user_message')
def handle_user_message(json):
    user_input = json.get("message", "")
    print("User said:", user_input)

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
                    {"role": "user", "content": user_input}
                ]
            }
        )

        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
        else:
            print("OpenRouter error:", response.text)
            reply = f"Error: OpenRouter returned status {response.status_code}"

    except Exception as e:
        print("Chatbot error:", str(e))
        reply = f"Error talking to chatbot: {str(e)}"

    emit("bot_reply", {"message": reply})


# Production Entrypoint
if __name__ == "__main__":
    import eventlet
    import eventlet.wsgi
    print("Starting socket-enabled Flask app with Eventlet...")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
