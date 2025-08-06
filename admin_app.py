from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import csv
import datetime
from shared.db_config import get_db_connection
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Set template folder
app.template_folder = 'admin_templates'

# ========== ROUTES ==========
@app.route('/')
def root():
    return redirect(url_for('admin_home'))
# Admin Home
@app.route('/admin')
def admin_home():
    return render_template('admin_home.html', now=datetime.now())

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = shared.db_config.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admin WHERE email = ? AND password = ?", (email, password))
        admin = cursor.fetchone()

        conn.close()

        if admin:
            session['admin'] = email
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid email or password.'
            return render_template('admin_login.html', error=error, now=datetime.now())

    return render_template('admin_login.html', now=datetime.now())


# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE hired=1")
    total_hires = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'admin_dashboard.html',
        admin=session['admin'],
        total_candidates=total_candidates,
        total_jobs=total_jobs,
        total_interviews=total_interviews,
        total_hires=total_hires,
        now=datetime.datetime.now()
    )

# Job Management
@app.route('/admin/jobs')
def admin_jobs():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    jobs = []
    csv_path = os.path.join('data', 'job_dataset.csv')
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)

    return render_template('admin_jobs.html', admin=session['admin'], jobs=jobs)

# Edit Job
@app.route('/admin/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    csv_path = os.path.join('data', 'job_dataset.csv')
    jobs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        jobs = list(reader)

    if request.method == 'POST':
        for job in jobs:
            if int(job['JobID']) == job_id:
                job['Title'] = request.form['title']
                job['Company'] = request.form['company']
                job['Location'] = request.form['location']
                job['Skills'] = request.form['skills']
                break

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)

        return redirect(url_for('admin_jobs'))

    job_data = next((job for job in jobs if int(job['JobID']) == job_id), None)
    return render_template('edit_job.html', admin=session['admin'], job=job_data)

# Communication Center
@app.route('/admin/communication')
def admin_communication():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    recent_messages = [
        {
            'to': 'john@example.com',
            'subject': 'Interview Confirmation',
            'date': 'July 29, 2025'
        },
        {
            'to': 'alice@example.com',
            'subject': 'Application Status',
            'date': 'July 27, 2025'
        }
    ]
    return render_template('admin_communication.html', admin=session['admin'], messages=recent_messages)

# Candidate Management
@app.route('/admin/candidates')
def admin_candidates():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users")
    candidates = cursor.fetchall()
    conn.close()

    return render_template('admin_candidates.html', admin=session['admin'], candidates=candidates)

# Analytics Page
@app.route('/admin/analytics')
def admin_analytics():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    registrations = [
        {'date': '2025-07-01', 'users': 5, 'jobs': 2},
        {'date': '2025-07-10', 'users': 8, 'jobs': 4},
        {'date': '2025-07-15', 'users': 12, 'jobs': 6},
        {'date': '2025-07-20', 'users': 10, 'jobs': 3},
        {'date': '2025-07-25', 'users': 15, 'jobs': 5},
    ]

    return render_template('admin_analytics.html', admin=session['admin'], data=registrations)


# ========== MAIN ==========
if __name__ == '__main__':
    app.run(debug=True)
