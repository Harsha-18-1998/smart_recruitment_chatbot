from flask import Flask, render_template, request, redirect, session, url_for
import os
import pandas as pd
from datetime import datetime, timedelta
import calendar
from shared.db_config import get_db_connection
import json
import csv
from collections import Counter
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import  flash, send_file
import smtplib
from email.mime.text import MIMEText
import sqlite3
import io
import matplotlib
from dotenv import load_dotenv
from email.message import EmailMessage

matplotlib.use('Agg')  # Use non-GUI backend

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.template_folder = 'admin_templates'

CSV_PATH = 'data/job_dataset.csv'

# ------------------ Utility Functions ------------------
def init_message_db():
    conn = sqlite3.connect('data/messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT,
                    subject TEXT,
                    message TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

init_message_db()

def load_jobs_from_csv():
    jobs = []
    try:
        with open('data/job_dataset.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                jobs.append({k.strip(): v.strip() for k, v in row.items()})
    except Exception as e:
        print("Error reading CSV:", e)
    return jobs

def get_total_applicants():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def get_total_job_titles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    db_jobs = cursor.fetchone()[0]
    conn.close()

    csv_jobs = 0
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.columns = df.columns.str.strip()
        if 'Job_Title' in df.columns:
            csv_jobs = df['Job_Title'].dropna().shape[0]

    return db_jobs + csv_jobs

def get_total_interviews():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def count_csv_jobs_between(start_date, end_date):
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.columns = df.columns.str.strip()
        if 'date_posted' in df.columns and 'Job_Title' in df.columns:
            df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
            mask = (df['date_posted'] >= start_date) & (df['date_posted'] <= end_date)
            return df.loc[mask, 'Job_Title'].dropna().shape[0]
    return 0

def calculate_growth(previous, current):
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 2)

# ------------------ Routes ------------------

@app.route('/')
def admin_home():
    return redirect('/admin')

@app.route('/admin')
def admin_main():
    return render_template("admin_home.html", now=datetime.now())

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE email=%s AND password=%s", (email, password))
        admin = cursor.fetchone()
        conn.close()
        if admin:
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            return redirect('/admin/dashboard')
        else:
            return render_template("admin_login.html", error="Invalid credentials", now=datetime.now())
    return render_template("admin_login.html", now=datetime.now())

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admin (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        conn.close()
        return redirect('/admin/login')
    return render_template("admin_signup.html", now=datetime.now())

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total applicants
    cursor.execute("SELECT COUNT(*) FROM users")
    total_applicants = cursor.fetchone()[0]

    # Total interviews
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]

    # Total jobs from DB
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_db_jobs = cursor.fetchone()[0]

    # Total jobs from CSV
    total_csv_jobs = 0
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.columns = df.columns.str.strip()
        if 'Job_Title' in df.columns:
            total_csv_jobs = df['Job_Title'].dropna().shape[0]

    total_jobs = total_db_jobs + total_csv_jobs

    # Dates
    today = datetime.today()
    first_day_this_month = today.replace(day=1)
    last_day_this_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)

    # Growth: Applicants
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date BETWEEN %s AND %s",
                   (first_day_this_month, last_day_this_month))
    applicants_this_month = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date BETWEEN %s AND %s",
                   (first_day_last_month, last_day_last_month))
    applicants_last_month = cursor.fetchone()[0]
    applicant_growth = calculate_growth(applicants_last_month, applicants_this_month)

    # Growth: Jobs
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE date_posted BETWEEN %s AND %s",
                   (first_day_this_month, last_day_this_month))
    jobs_this_month_db = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE date_posted BETWEEN %s AND %s",
                   (first_day_last_month, last_day_last_month))
    jobs_last_month_db = cursor.fetchone()[0]
    jobs_this_month_csv = count_csv_jobs_between(first_day_this_month, last_day_this_month)
    jobs_last_month_csv = count_csv_jobs_between(first_day_last_month, last_day_last_month)
    jobs_this_month = jobs_this_month_db + jobs_this_month_csv
    jobs_last_month = jobs_last_month_db + jobs_last_month_csv
    jobs_growth = calculate_growth(jobs_last_month, jobs_this_month)

    # Growth: Interviews
    cursor.execute("SELECT COUNT(*) FROM interviews WHERE interview_date BETWEEN %s AND %s",
                   (first_day_this_month, last_day_this_month))
    interviews_this_month = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM interviews WHERE interview_date BETWEEN %s AND %s",
                   (first_day_last_month, last_day_last_month))
    interviews_last_month = cursor.fetchone()[0]
    interview_growth = calculate_growth(interviews_last_month, interviews_this_month)

    conn.close()

    return render_template(
        'admin_dashboard.html',
        total_applicants=total_applicants,
        total_jobs=total_jobs,
        total_interviews=total_interviews,
        applicant_growth=applicant_growth,
        jobs_growth=jobs_growth,
        interview_growth=interview_growth
    )

@app.route('/admin/jobs', methods=['GET'])
def admin_jobs():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    jobs = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append({k.strip(): v.strip() for k, v in row.items()})

    return render_template("admin_jobs.html", jobs=jobs, now=datetime.now())

@app.route('/admin/add_job', methods=['POST'])
def add_job():
    jobs = load_jobs_from_csv()

    # Get max Job_ID
    existing_ids = [int(job['Job_ID']) for job in jobs if job['Job_ID'].isdigit()]
    new_id = max(existing_ids, default=0) + 1

    new_job = {
        'Job_ID': str(new_id),
        'Job_Title': request.form['title'],
        'Skills': request.form['skills'],
        'date_posted': datetime.now().strftime('%Y-%m-%d')
    }

    # Append to CSV
    with open('data/job_dataset.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Job_ID', 'Job_Title', 'Skills', 'date_posted'])
        if file.tell() == 0:  # if file is empty
            writer.writeheader()
        writer.writerow(new_job)

    return redirect(url_for('admin_jobs'))


@app.route('/admin/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        title = request.form['title']
        skills = request.form['skills']
        cursor.execute("UPDATE jobs SET title=%s, skills=%s WHERE id=%s", (title, skills, job_id))
        conn.commit()
        conn.close()
        return redirect('/admin/jobs')

    cursor.execute("SELECT * FROM jobs WHERE id=%s", (job_id,))
    job = cursor.fetchone()
    conn.close()
    return render_template("edit_job.html", job=job, now=datetime.now())

@app.route('/admin/update_job/<job_id>', methods=['POST'])
def update_job(job_id):
    updated_title = request.form['title']
    updated_skills = request.form['skills']
    updated_description = request.form.get('description', '')

    jobs = load_jobs_from_csv()
    for job in jobs:
        if job['Job_ID'] == job_id:
            job['Job_Title'] = updated_title
            job['Skills'] = updated_skills
            job['Description'] = updated_description
            break

    # Overwrite the CSV
    with open('data/job_dataset.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Job_ID', 'Job_Title', 'Skills', 'date_posted'])
        writer.writeheader()
        writer.writerows(jobs)

    return redirect(url_for('admin_jobs'))


@app.route('/admin/delete_job/<job_id>', methods=['POST'])
def delete_job(job_id):
    jobs = load_jobs_from_csv()
    updated_jobs = [job for job in jobs if job['Job_ID'] != job_id]

    # Overwrite the CSV with updated job list
    with open('data/job_dataset.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Job_ID', 'Job_Title', 'Skills', 'date_posted'])
        writer.writeheader()
        writer.writerows(updated_jobs)

    return redirect(url_for('admin_jobs'))


@app.route('/admin/candidates')
def admin_candidates():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    candidates = cursor.fetchall()
    conn.close()
    return render_template("admin_candidates.html", candidates=candidates, now=datetime.now())

from flask import render_template
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime
from shared.db_config import get_db_connection

@app.route('/admin/analytics')
def admin_analytics():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total users
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    # Total interviews
    cursor.execute("SELECT COUNT(*) AS total_interviews FROM interviews")
    total_interviews = cursor.fetchone()['total_interviews']

    # AI match accuracy
    cursor.execute("SELECT AVG(match_accuracy) AS avg_accuracy FROM interviews")
    avg_accuracy_row = cursor.fetchone()
    match_accuracy = round(avg_accuracy_row['avg_accuracy'], 2) if avg_accuracy_row['avg_accuracy'] else 0

    # Load job data from CSV
    job_dates_raw = []
    total_jobs = 0
    try:
        df = pd.read_csv('data/job_dataset.csv')
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all')  # Drop empty rows
        total_jobs = len(df)

        date_col = None
        for col in df.columns:
            if col.strip() == 'date_posted':
                date_col = col
                break

        if date_col:
            for date_str in df[date_col].dropna():
                try:
                    parsed_date = datetime.strptime(date_str.strip(), "%d-%m-%Y")
                    job_dates_raw.append(parsed_date.date())
                except ValueError:
                    continue
    except Exception as e:
        print("Error reading job_dataset.csv:", e)

    # Prepare Job Posting Trend data
    job_date_counts = {}
    for date in job_dates_raw:
        job_date_counts[date] = job_date_counts.get(date, 0) + 1

    sorted_job_data = sorted(job_date_counts.items())
    job_dates_x = [d.strftime("%Y-%m-%d") for d, _ in sorted_job_data]
    job_counts_y = [c for _, c in sorted_job_data]

    # Prepare User Registrations Over Time
    cursor.execute("SELECT registration_date FROM users WHERE registration_date IS NOT NULL")
    reg_dates_raw = [row['registration_date'] for row in cursor.fetchall()]
    user_date_counts = {}
    for dt in reg_dates_raw:
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d")
        date_only = dt.date()
        user_date_counts[date_only] = user_date_counts.get(date_only, 0) + 1

    sorted_user_data = sorted(user_date_counts.items())
    reg_dates_x = [d.strftime("%Y-%m-%d") for d, _ in sorted_user_data]
    reg_counts_y = [c for _, c in sorted_user_data]

    conn.close()

    return render_template('admin_analytics.html',
                           total_users=total_users,
                           total_jobs=total_jobs,
                           total_interviews=total_interviews,
                           ai_match_accuracy=match_accuracy,
                           reg_dates=json.dumps(reg_dates_x),
                           reg_counts=json.dumps(reg_counts_y),
                           job_dates=json.dumps(job_dates_x),
                           job_counts=json.dumps(job_counts_y))

@app.route('/admin/communication', methods=['GET', 'POST'])
def admin_communication():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        recipient = request.form['recipient']
        subject = request.form['subject']
        body = request.form['body']

        try:
            # Read environment variables for sender email and app password
            sender = os.getenv("EMAIL_SENDER")
            password = os.getenv("EMAIL_PASSWORD")

            # Prepare and send email
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            msg.set_content(body)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)

            # Store message in database
            cursor.execute("""
                INSERT INTO messages (sender_email, receiver_email, subject, content, sent_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (sender, recipient, subject, body, datetime.now()))
            conn.commit()

            flash('✅ Email sent successfully!', 'success')

        except Exception as e:
            flash(f'❌ Failed to send email: {str(e)}', 'danger')

    # Fetch and display messages in reverse chronological order
    cursor.execute("SELECT * FROM messages ORDER BY sent_at DESC")
    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_communication.html', messages=messages)



if __name__ == '__main__':
    app.run(debug=True)
