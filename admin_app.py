from flask import Flask, render_template, request, redirect, session, url_for
import os
import pandas as pd
from datetime import datetime, timedelta
import calendar
from shared.db_config import get_db_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.template_folder = 'admin_templates'

CSV_PATH = 'data/job_dataset.csv'


# ========== Admin Routes ==========

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


# ========== Dashboard ==========

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total applicants
    cursor.execute("SELECT COUNT(*) FROM users")
    total_applicants = cursor.fetchone()[0]

    # Total interviews
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]

    # Total jobs (DB + CSV)
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_db_jobs = cursor.fetchone()[0]
    csv_jobs = pd.read_csv(CSV_PATH)
    total_csv_jobs = len(csv_jobs)
    total_jobs = total_db_jobs + total_csv_jobs

    # Date Ranges
    today = datetime.today()
    first_day_this_month = today.replace(day=1)
    last_day_this_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)

    # Applicants Growth
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date BETWEEN %s AND %s", (first_day_this_month, last_day_this_month))
    applicants_this_month = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date BETWEEN %s AND %s", (first_day_last_month, last_day_last_month))
    applicants_last_month = cursor.fetchone()[0]
    applicant_growth = calculate_growth(applicants_last_month, applicants_this_month)

    # Jobs Growth (DB + CSV)
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE date_posted BETWEEN %s AND %s", (first_day_this_month, last_day_this_month))
    jobs_this_month_db = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE date_posted BETWEEN %s AND %s", (first_day_last_month, last_day_last_month))
    jobs_last_month_db = cursor.fetchone()[0]

    # CSV jobs growth
    def count_csv_jobs_between(start_date, end_date):
        csv_jobs['date_posted'] = pd.to_datetime(csv_jobs['date_posted'], errors='coerce')
        return len(csv_jobs[(csv_jobs['date_posted'] >= start_date) & (csv_jobs['date_posted'] <= end_date)])

    jobs_this_month_csv = count_csv_jobs_between(first_day_this_month, last_day_this_month)
    jobs_last_month_csv = count_csv_jobs_between(first_day_last_month, last_day_last_month)

    jobs_this_month = jobs_this_month_db + jobs_this_month_csv
    jobs_last_month = jobs_last_month_db + jobs_last_month_csv
    jobs_growth = calculate_growth(jobs_last_month, jobs_this_month)

    # Interview Growth
    cursor.execute("SELECT COUNT(*) FROM interviews WHERE interview_date BETWEEN %s AND %s", (first_day_this_month, last_day_this_month))
    interviews_this_month = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM interviews WHERE interview_date BETWEEN %s AND %s", (first_day_last_month, last_day_last_month))
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


# Growth helper
def calculate_growth(previous, current):
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100)


# ========== Job Management ==========

@app.route('/admin/jobs')
def admin_jobs():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs")
    jobs_db = cursor.fetchall()
    conn.close()

    csv_jobs = pd.read_csv(CSV_PATH).to_dict(orient='records')

    return render_template("admin_jobs.html", jobs_db=jobs_db, jobs_csv=csv_jobs, now=datetime.now())


@app.route('/admin/jobs/add', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        title = request.form['title']
        skills = request.form['skills']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs (title, skills, date_posted) VALUES (%s, %s, %s)", (title, skills, datetime.today()))
        conn.commit()
        conn.close()
        return redirect('/admin/jobs')
    return render_template("add_job.html", now=datetime.now())


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


@app.route('/admin/jobs/delete/<int:job_id>')
def delete_job(job_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/jobs')


# ========== Other Pages ==========

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


@app.route('/admin/analytics')
def admin_analytics():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    return render_template("admin_analytics.html", now=datetime.now())


@app.route('/admin/communication')
def admin_communication():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    return render_template("admin_communication.html", now=datetime.now())


# ========== Run App ==========

if __name__ == '__main__':
    app.run(debug=True)
