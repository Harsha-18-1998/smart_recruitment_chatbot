from flask import Flask, render_template, request, session, redirect, url_for, flash
from database.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_admin_secret_key_here'

# ----------------- 🔐 ADMIN AUTH ------------------

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin'] = admin['username']
            flash("Admin login successful.")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials.")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash("Admin logged out.")
    return redirect(url_for('admin_login'))

# ----------------- 🛠 ADMIN PANEL (MySQL) ------------------

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cursor.execute("INSERT INTO jobs (title, description) VALUES (%s, %s)", (title, description))
        conn.commit()
        flash("Job added successfully.")
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', jobs=jobs)

@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        new_title = request.form['title']
        new_description = request.form['description']
        cursor.execute("UPDATE jobs SET title = %s, description = %s WHERE job_id = %s",
                       (new_title, new_description, job_id))
        conn.commit()
        flash('Job updated successfully.')
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cursor.fetchone()
    cursor.close()
    conn.close()

    if job:
        return render_template('edit_job.html', job=job)
    else:
        return "Job not found", 404

@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Job deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/')
def home():
    return redirect(url_for('admin_login'))


# ----------------- 🚀 RUN ADMIN APP ------------------

if __name__ == '__main__':
    app.run(debug=True, port=5001)
