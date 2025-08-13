from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import csv
from datetime import datetime
from shared.db_config import get_db_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.template_folder = 'admin_templates'

# ========== ROUTES ==========

@app.route('/')
def root():
    return redirect(url_for('admin_home'))

@app.route('/admin')
def admin_home():
    return render_template('admin_home.html', now=datetime.now())

# -------- ADMIN SIGNUP --------
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        existing_admin = cursor.fetchone()

        if existing_admin:
            conn.close()
            error = 'Admin with this email already exists.'
            return render_template('admin_signup.html', error=error, now=datetime.now())

        cursor.execute("INSERT INTO admin (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        conn.close()

        flash('Admin registered successfully. Please log in.')
        return redirect(url_for('admin_login'))

    return render_template('admin_signup.html', now=datetime.now())

# -------- ADMIN LOGIN --------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if email exists
        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        admin = cursor.fetchone()

        if not admin:
            conn.close()
            return render_template('admin_login.html', error='Email not registered', now=datetime.now())

        if admin['password'] != password:
            conn.close()
            return render_template('admin_login.html', error='Incorrect password', now=datetime.now())

        # Login successful
        session['admin'] = admin['email']
        conn.close()
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html', now=datetime.now())


# -------- ADMIN LOGOUT --------
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# -------- ADMIN DASHBOARD --------
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
        now=datetime.now()
    )

# -------- JOB MANAGEMENT --------
@app.route('/admin/jobs')
def admin_jobs():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    csv_path = os.path.join('data', 'job_dataset.csv')
    jobs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            row['JobID'] = i
            jobs.append(row)

    return render_template('admin_jobs.html', admin=session['admin'], jobs=jobs, now=datetime.now())


@app.route('/admin/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    csv_path = os.path.join('data', 'job_dataset.csv')

    # Read jobs and add JobID dynamically
    jobs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            row['JobID'] = str(i)  # Add JobID dynamically
            jobs.append(row)

    # Find the job to edit
    job_data = next((job for job in jobs if int(job['JobID']) == job_id), None)

    if not job_data:
        return "Job not found", 404

    if request.method == 'POST':
        # Update job details from form
        job_data['Job Title'] = request.form['title']
        job_data['Skills'] = request.form['skills']

        # Write updated jobs list back to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Job Title', 'Skills'])
            writer.writeheader()
            for job in jobs:
                writer.writerow({'Job Title': job['Job Title'], 'Skills': job['Skills']})

        return redirect(url_for('admin_jobs'))

    return render_template('edit_job.html', job=job_data, now=datetime.now())

@app.route('/admin/jobs/delete/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    csv_path = os.path.join('data', 'job_dataset.csv')

    # Load existing jobs with JobID assigned
    jobs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            row['JobID'] = str(i)
            jobs.append(row)

    # Remove the job with matching JobID
    jobs = [job for job in jobs if int(job['JobID']) != job_id]

    # Save updated list (without JobID column in CSV)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Job Title', 'Skills'])
        writer.writeheader()
        for job in jobs:
            writer.writerow({'Job Title': job['Job Title'], 'Skills': job['Skills']})

    return redirect(url_for('admin_jobs'))


# -------- COMMUNICATION --------
@app.route('/admin/communication')
def admin_communication():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    recent_messages = [
        {'to': 'john@example.com', 'subject': 'Interview Confirmation', 'date': 'July 29, 2025'},
        {'to': 'alice@example.com', 'subject': 'Application Status', 'date': 'July 27, 2025'}
    ]
    return render_template('admin_communication.html', admin=session['admin'], messages=recent_messages, now=datetime.now())

# -------- CANDIDATES --------
@app.route('/admin/candidates')
def admin_candidates():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users")
    candidates = cursor.fetchall()
    conn.close()

    return render_template('admin_candidates.html', admin=session['admin'], candidates=candidates, now=datetime.now())

# -------- ANALYTICS --------
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

    return render_template('admin_analytics.html', admin=session['admin'], data=registrations, now=datetime.now())

# ========== MAIN ==========
if __name__ == '__main__':
    app.run(debug=True)
