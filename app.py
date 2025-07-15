from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from scripts.resume_parser import extract_skills
from scripts.job_matcher import match_resume_to_jobs, get_job_info_reply
from database.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)

# ----------------- ✅ USER INTERFACE ------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    file = request.files['resume']

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

    html = f"""
    <h2>Resume Uploaded Successfully!</h2>
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Extracted Skills:</strong> {', '.join(skills)}</p>
    <h3>Top Matching Jobs:</h3>
    <ul>
    """
    for row in matches:
        html += f"<li><b>{row['title']}</b>: {row['description']} (Match Score: {round(row['score'], 2)}%)</li>"
    html += "</ul>"
    return html

@app.route('/dashboard')
def user_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, email, skills, top_jobs, timestamp
        FROM resume_submissions
        WHERE email = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (email,))
    latest = cursor.fetchone()
    cursor.close()
    conn.close()

    if not latest:
        return "No data found for this email."

    return render_template('user_dashboard.html', data=latest)

# ----------------- 💬 CHATBOT ------------------

@socketio.on('user_message')
def handle_user_message(data):
    user_msg = data['message']
    print("User:", user_msg)

    bot_reply = get_job_info_reply(user_msg)
    emit('bot_reply', {'message': bot_reply})

# ----------------- 🔐 USER AUTH ------------------

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
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out.")
    return redirect(url_for('login'))

# ----------------- 🚀 RUN ------------------

if __name__ == '__main__':
    socketio.run(app, debug=True)
