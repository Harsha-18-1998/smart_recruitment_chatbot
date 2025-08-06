import os
import pandas as pd
import nltk
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from shared.resume_parser import extract_skills, extract_text
from shared.db_config import get_db_connection
from shared.chatbot_engine import get_job_info_reply
from shared.mock_interview_engine import load_questions  # Should be updated to accept role + subject

# Setup Flask and SocketIO
app = Flask(__name__, template_folder='user_templates')

# Setup nltk path
nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "defaultsecret")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

app.config['SECRET_KEY'] = FLASK_SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash("All fields are required.")
            return redirect(url_for('signup'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email already registered.")
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already taken.")
            cursor.close()
            conn.close()
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Signup successful. Please log in.")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

@app.route('/dashboard')
def user_dashboard():
    if 'username' not in session:
        flash("Login required.")
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session['username'], email=session['email'])

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_name = request.form['username']
        new_email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username=%s, email=%s WHERE id=%s",
                       (new_name, new_email, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()

        session['username'] = new_name
        session['email'] = new_email
        flash("Profile updated.")

    return render_template('profile.html', username=session.get('username'), email=session.get('email'))

@app.route('/resume_upload', methods=['GET', 'POST'])
def resume_upload():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file uploaded.")
            return redirect(request.url)

        resume = request.files['resume']
        if resume.filename == '':
            flash("Empty filename.")
            return redirect(request.url)

        filepath = os.path.join('uploads', resume.filename)
        os.makedirs('uploads', exist_ok=True)
        resume.save(filepath)

        text = extract_text(filepath)
        resume_skills = extract_skills(text)

        job_df = pd.read_csv('data/job_dataset.csv')

        matched_jobs = set()
        for _, row in job_df.iterrows():
            job_skills = [s.strip().lower() for s in row['Skills'].split(',')]
            match_count = sum(1 for skill in resume_skills if skill.lower() in job_skills)
            if match_count > 0:
                matched_jobs.add(row['Job Title'])

        matched_jobs = list(matched_jobs)

        return render_template('resume_result.html',
                               skills=resume_skills,
                               matched_jobs=matched_jobs)

    return render_template('resume_upload.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    reply = get_job_info_reply(user_message)
    return jsonify({'reply': reply})

# ---------------- Mock Interview UI ----------------

@app.route('/mock_interview', methods=['GET', 'POST'])
def mock_interview():
    if 'username' not in session:
        flash("Login required.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Determine if user selected role or subject
        choice = request.form.get('choice')
        role = None
        subject = None
        if choice == 'role':
            role = request.form.get('role')
            if not role:
                flash("Please select a Job Role.")
                return redirect(url_for('mock_interview'))
        elif choice == 'subject':
            subject = request.form.get('subject')
            if not subject:
                flash("Please select a Subject.")
                return redirect(url_for('mock_interview'))
        else:
            flash("Please select either Job Role or Subject.")
            return redirect(url_for('mock_interview'))

        # Load questions based on either role or subject
        questions = load_questions(role=role, subject=subject)
        if not questions:
            flash("No questions found for your selection.")
            return redirect(url_for('mock_interview'))

        session['mock_role'] = role
        session['mock_subject'] = subject
        session['mock_questions'] = questions
        session['mock_index'] = 0
        session['mock_answers'] = []

        return redirect(url_for('mock_interview_question'))

    return render_template(
        'mock_interview.html',
        interview_started=False,
        selected_role=session.get('mock_role'),
        selected_subject=session.get('mock_subject')
    )


@app.route('/mock_interview/question', methods=['GET', 'POST'])
def mock_interview_question():
    if 'username' not in session:
        flash("Login required.")
        return redirect(url_for('login'))

    questions = session.get('mock_questions')
    index = session.get('mock_index', 0)
    answers = session.get('mock_answers', [])
    role = session.get('mock_role')
    subject = session.get('mock_subject')

    if not questions or (role is None and subject is None):
        flash("Start interview by selecting a role or subject.")
        return redirect(url_for('mock_interview'))

    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        if not answer:
            flash("Please provide an answer before continuing.")
            question = questions[index]
            return render_template(
                'mock_interview.html',
                interview_started=True,
                selected_role=role,
                selected_subject=subject,
                current_index=index,
                total_questions=len(questions),
                question=question,
                previous_answer='',
            )

        answers.append(answer)
        session['mock_answers'] = answers
        index += 1
        session['mock_index'] = index

        if index >= len(questions):
            # Interview completed - show summary page
            return render_template('mock_interview_complete.html',
                                   role=role,
                                   subject=subject,
                                   answers=answers)

    question = questions[index] if index < len(questions) else None

    return render_template('mock_interview.html',
                           interview_started=True,
                           selected_role=role,
                           selected_subject=subject,
                           current_index=index,
                           total_questions=len(questions),
                           question=question,
                           previous_answer='')


@app.route('/mock_interview/reset')
def mock_interview_reset():
    session.pop('mock_role', None)
    session.pop('mock_subject', None)
    session.pop('mock_questions', None)
    session.pop('mock_index', None)
    session.pop('mock_answers', None)
    flash("Mock interview session reset.")
    return redirect(url_for('mock_interview'))

# ---------------- Run ----------------
if __name__ == "__main__":
    import eventlet
    print("App running at http://localhost:10000")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
