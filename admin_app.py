# from flask import Flask, render_template, request, session, redirect, url_for, flash # admin can upload job dataset csv file after
# from database.db_config import get_db_connection
# from werkzeug.security import generate_password_hash, check_password_hash
# import pandas as pd

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_admin_secret_key_here'

# # ----------------- 🔐 ADMIN AUTH ------------------

# @app.route('/admin_login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
#         admin = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if admin and check_password_hash(admin['password'], password):
#             session['admin'] = admin['username']
#             flash("Admin login successful.")
#             return redirect(url_for('admin_dashboard'))
#         else:
#             flash("Invalid admin credentials.")
#             return redirect(url_for('admin_login'))

#     return render_template('admin_login.html')


# @app.route('/admin_logout')
# def admin_logout():
#     session.pop('admin', None)
#     flash("Admin logged out.")
#     return redirect(url_for('admin_login'))

# # ----------------- 🛠 ADMIN PANEL ------------------

# @app.route('/admin_dashboard', methods=['GET', 'POST'])
# def admin_dashboard():
#     if 'admin' not in session:
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     if request.method == 'POST':
#         if 'title' in request.form:
#             # Manual job add
#             title = request.form['title']
#             description = request.form['description']
#             cursor.execute("INSERT INTO jobs (title, description) VALUES (%s, %s)", (title, description))
#             conn.commit()
#             flash("Job added successfully.")

#         elif 'csv_file' in request.files:
#             # CSV upload
#             file = request.files['csv_file']
#             if file.filename.endswith('.csv'):
#                 df = pd.read_csv(file)
#                 if 'title' in df.columns and 'description' in df.columns:
#                     for _, row in df.iterrows():
#                         cursor.execute("INSERT INTO jobs (title, description) VALUES (%s, %s)",
#                                        (row['title'], row['description']))
#                     conn.commit()
#                     flash("CSV imported successfully.")
#                 else:
#                     flash("CSV must have 'title' and 'description' columns.")
#             else:
#                 flash("Please upload a valid CSV file.")

#         return redirect(url_for('admin_dashboard'))

#     cursor.execute("SELECT * FROM jobs")
#     jobs = cursor.fetchall()
#     cursor.close()
#     conn.close()

#     return render_template('admin.html', jobs=jobs)

# @app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
# def edit_job(job_id):
#     if 'admin' not in session:
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     if request.method == 'POST':
#         new_title = request.form['title']
#         new_description = request.form['description']
#         cursor.execute("UPDATE jobs SET title = %s, description = %s WHERE job_id = %s",
#                        (new_title, new_description, job_id))
#         conn.commit()
#         flash('Job updated successfully.')
#         return redirect(url_for('admin_dashboard'))

#     cursor.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
#     job = cursor.fetchone()
#     cursor.close()
#     conn.close()

#     if job:
#         return render_template('edit_job.html', job=job)
#     else:
#         return "Job not found", 404

# @app.route('/delete_job/<int:job_id>', methods=['POST'])
# def delete_job(job_id):
#     if 'admin' not in session:
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
#     conn.commit()
#     cursor.close()
#     conn.close()
#     flash('Job deleted successfully.')
#     return redirect(url_for('admin_dashboard'))

# @app.route('/')
# def home():
#     return redirect(url_for('admin_login'))

# # ----------------- 🚀 RUN ADMIN APP ------------------

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)


# from flask import Flask, render_template, request, session, redirect, url_for, flash
# from shared.db_config import get_db_connection
# from werkzeug.security import generate_password_hash, check_password_hash
# import pandas as pd
# import os

# app = Flask(__name__, template_folder='admin_templates')
# app.config['SECRET_KEY'] = 'your_admin_secret_key_here'

# CSV_PATH = 'data/job_dataset.csv'
# os.makedirs('data', exist_ok=True)

# # ----------------- 🔐 ADMIN AUTH ------------------

# @app.route('/admin_login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
#         admin = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if admin and check_password_hash(admin['password'], password):
#             session['admin'] = admin['username']
#             flash("Admin login successful.")
#             return redirect(url_for('admin_dashboard'))
#         else:
#             flash("Invalid admin credentials.")
#             return redirect(url_for('admin_login'))

#     return render_template('admin_login.html')


# @app.route('/admin_logout')
# def admin_logout():
#     session.pop('admin', None)
#     flash("Admin logged out.")
#     return redirect(url_for('admin_login'))

# # ----------------- 🛠 ADMIN PANEL USING CSV ------------------

# @app.route("/admin", methods=["GET", "POST"])
# def admin_dashboard():
#     if request.method == "POST":
#         # Add Job or Import CSV
#         if 'csv_file' in request.files:
#             file = request.files['csv_file']
#             df = pd.read_csv(file)
#             for _, row in df.iterrows():
#                 job = Job(title=row['Title'], description=row['Description'])
#                 db.session.add(job)
#             db.session.commit()
#             flash("Jobs imported successfully")
#         else:
#             title = request.form['title']
#             desc = request.form['description']
#             db.session.add(Job(title=title, description=desc))
#             db.session.commit()
#             flash("Job added successfully")
#         return redirect("/admin")

#     # Filters
#     search = request.args.get("search", "").lower()
#     category = request.args.get("category", "")
#     jobs = Job.query
#     if search:
#         jobs = jobs.filter(Job.title.ilike(f"%{search}%"))
#     if category:
#         jobs = jobs.filter(Job.category == category)
#     jobs = jobs.all()

#     # Chart data
#     chart_data = {
#         "labels": [j.title for j in jobs],
#         "counts": [1 for _ in jobs]
#     }

#     return render_template("admin.html",
#         jobs=jobs,
#         total_jobs=Job.query.count(),
#         total_resumes=Resume.query.count(),
#         total_matches=Match.query.count(),
#         chart_data=chart_data
#     )

# @app.route("/export_jobs_csv", methods=["POST"])
# def export_jobs_csv():
#     jobs = Job.query.all()
#     output = StringIO()
#     writer = csv.writer(output)
#     writer.writerow(['ID', 'Title', 'Description'])
#     for j in jobs:
#         writer.writerow([j.job_id, j.title, j.description])
#     response = make_response(output.getvalue())
#     response.headers["Content-Disposition"] = "attachment; filename=jobs.csv"
#     response.headers["Content-type"] = "text/csv"
#     return response

# @app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
# def edit_job(job_id):
#     if 'admin' not in session:
#         return redirect(url_for('admin_login'))

#     df = pd.read_csv(CSV_PATH)

#     if request.method == 'POST':
#         new_title = request.form['title']
#         new_description = request.form['description']

#         df.loc[df['job_id'] == job_id, 'title'] = new_title
#         df.loc[df['job_id'] == job_id, 'description'] = new_description
#         df.to_csv(CSV_PATH, index=False)

#         flash('Job updated successfully.')
#         return redirect(url_for('admin_dashboard'))

#     job = df[df['job_id'] == job_id].to_dict(orient='records')
#     if job:
#         return render_template('edit_job.html', job=job[0])
#     else:
#         return "Job not found", 404

# @app.route('/delete_job/<int:job_id>', methods=['POST'])
# def delete_job(job_id):
#     if 'admin' not in session:
#         return redirect(url_for('admin_login'))

#     df = pd.read_csv(CSV_PATH)
#     df = df[df['job_id'] != job_id]
#     df.to_csv(CSV_PATH, index=False)

#     flash('Job deleted successfully.')
#     return redirect(url_for('admin_dashboard'))

# @app.route('/')
# def home():
#     return redirect(url_for('admin_login'))

# # ----------------- 🚀 RUN ADMIN APP ------------------

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)


from flask import Flask, render_template, request, session, redirect, url_for, flash, make_response
from shared.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os, csv
from io import StringIO

app = Flask(__name__, template_folder='admin_templates')
app.config['SECRET_KEY'] = 'your_admin_secret_key_here'

CSV_PATH = 'data/job_dataset.csv'
os.makedirs('data', exist_ok=True)

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

# ----------------- 🛠 ADMIN PANEL ------------------

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Load jobs from CSV
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=['job_id', 'title', 'description'])

    if request.method == 'POST':
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            new_df = pd.read_csv(file)
            if 'title' in new_df.columns and 'description' in new_df.columns:
                new_df['job_id'] = range(df['job_id'].max() + 1 if not df.empty else 1,
                                         (df['job_id'].max() if not df.empty else 0) + len(new_df) + 1)
                df = pd.concat([df, new_df[['job_id', 'title', 'description']]], ignore_index=True)
                flash("CSV imported successfully.")
            else:
                flash("CSV must contain 'title' and 'description' columns.")
        else:
            title = request.form['title']
            description = request.form['description']
            job_id = df['job_id'].max() + 1 if not df.empty else 1
            new_job = pd.DataFrame([[job_id, title, description]], columns=['job_id', 'title', 'description'])
            df = pd.concat([df, new_job], ignore_index=True)
            flash("Job added successfully.")

        df.to_csv(CSV_PATH, index=False)
        return redirect(url_for('admin_dashboard'))

    search = request.args.get("search", "").lower()
    if search:
        filtered_df = df[df['title'].str.lower().str.contains(search)]
    else:
        filtered_df = df

    chart_data = {
        "labels": filtered_df['title'].tolist(),
        "counts": [1] * len(filtered_df)
    }

    return render_template("admin.html",
                           jobs=filtered_df.to_dict(orient='records'),
                           total_jobs=len(df),
                           total_resumes=50,  # dummy value
                           total_matches=25,  # dummy value
                           chart_data=chart_data)

@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    df = pd.read_csv(CSV_PATH)

    if request.method == 'POST':
        new_title = request.form['title']
        new_description = request.form['description']
        df.loc[df['job_id'] == job_id, ['title', 'description']] = [new_title, new_description]
        df.to_csv(CSV_PATH, index=False)
        flash('Job updated successfully.')
        return redirect(url_for('admin_dashboard'))

    job = df[df['job_id'] == job_id].to_dict(orient='records')
    return render_template('edit_job.html', job=job[0] if job else {})

@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    df = pd.read_csv(CSV_PATH)
    df = df[df['job_id'] != job_id]
    df.to_csv(CSV_PATH, index=False)
    flash('Job deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/export_jobs_csv', methods=['POST'])
def export_jobs_csv():
    df = pd.read_csv(CSV_PATH)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['job_id', 'title', 'description'])
    writer.writerows(df.values)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=jobs.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/')
def home():
    return redirect(url_for('admin_login'))

# ----------------- 🚀 RUN ADMIN APP ------------------

if __name__ == '__main__':
    app.run(debug=True, port=5001)