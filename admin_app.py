import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from shared.db_config import get_db_connection

load_dotenv()

app = Flask(__name__, template_folder='admin_templates', static_folder='static')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")


# Admin Login (GET + POST)
@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
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
            flash("Invalid credentials.")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


# Admin Signup (Optional)
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Admin signup successful. Please login.")
        return redirect(url_for('admin_login'))

    return render_template('admin_signup.html')


# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash("Login required.")
        return redirect(url_for('admin_login'))

    return render_template('admin_dashboard.html')


# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("Logged out.")
    return redirect(url_for('admin_login'))


# Run Admin App
if __name__ == "__main__":
    app.run(debug=True, port=5001)
 