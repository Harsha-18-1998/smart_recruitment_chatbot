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
import nltk

# Setup
nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))
load_dotenv()

# Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "defaultsecret")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

# Flask App
app = Flask(__name__, template_folder='user_templates')
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
            conn.commit()
            flash("Account created successfully.")
            return redirect(url_for('login'))
        except:
            flash("User already exists.")
            return redirect(url_for('signup'))
        finally:
            cursor.close()
            conn.close()

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['email'] = user['email']
            flash("Login successful.")
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

@app.route('/dashboard')
def user_dashboard():
    if 'user' not in session:
        flash("Login required.")
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', user=session['user'])

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_name = request.form['username']
        new_email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username=%s, email=%s WHERE email=%s", (new_name, new_email, session['email']))
        conn.commit()
        cursor.close()
        conn.close()

        session['user'] = new_name
        session['email'] = new_email
        flash("Profile updated successfully.")

    return render_template('profile.html', username=session.get('user'), email=session.get('email'))

@app.route('/resume_upload', methods=['GET', 'POST'])
def resume_upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['resume']
        if not file:
            flash("No file uploaded.")
            return redirect(request.url)

        resume_text = file.read().decode('utf-8')
        skills = extract_skills(resume_text)
        matches = match_resume_to_jobs(skills)
        top_jobs = matches[:5]

        return render_template('resume_result.html', name=session['user'], email=session['email'],
                               skills=skills, top_jobs=top_jobs)

    return render_template('resume_upload.html')

@app.route('/mock_interview')
def mock_interview():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('mock_interview.html')

# ---------------- Chatbot Socket ----------------

@socketio.on('user_message')
def handle_user_message(json):
    user_input = json.get("message", "")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": RENDER_URL,
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
        reply = response.json()["choices"][0]["message"]["content"] if response.status_code == 200 else f"API error {response.status_code}"
    except Exception as e:
        reply = f"Error talking to chatbot: {str(e)}"

    emit("bot_reply", {"message": reply})

# ---------------- Run App ----------------

if __name__ == "__main__":
    import eventlet
    print("App running at http://localhost:10000")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
