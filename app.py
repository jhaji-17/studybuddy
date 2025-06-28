import sqlite3
import os
import datetime
import humanize
import random
import sys
from datetime import timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, g, flash, send_from_directory
from dotenv import load_dotenv

# --- NEW: Import SendGrid libraries ---
import sendgrid
from sendgrid.helpers.mail import Mail

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configuration Section ---

# Set a secret key for session management
app.secret_key = os.getenv('SECRET_KEY', 'a_default_fallback_key_for_development')

# Define the absolute path for the database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'users.db')

# Configure file uploads
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# --- REMOVED: Flask-Mail Configuration and Initialization is no longer needed ---
# app.config['MAIL_SERVER'] = ...
# mail = Mail(app)
# ---


# --- NEW: Helper function to send email via SendGrid API ---
def send_verification_email(recipient_email, username, verification_code):
    message = Mail(
        from_email=os.getenv('MAIL_DEFAULT_SENDER'),
        to_emails=recipient_email,
        subject='Your StudyBuddy Verification Code',
        plain_text_content=f"Hello {username},\n\nWelcome to StudyBuddy!\n\nYour verification code is: {verification_code}\n\nThis code will expire in 15 minutes.\n\nThank you,\nThe StudyBuddy Team"
    )
    try:
        sg = sendgrid.SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"SendGrid response status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email with SendGrid API: {e}", file=sys.stderr)
        return False


# --- Database Helper Functions (Unchanged) ---
def get_db():
    # ... (rest of the function is the same)
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    # ... (this function is the same)
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ... (all your other functions like init_db, log_activity, etc. are unchanged)
# ...
# --- Database Initialization Command ---
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Clears the existing data and creates new tables."""
    init_db()
    print('Initialized the database.')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f'Created upload folder at: {UPLOAD_FOLDER}')

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_activity(user_id, action_type, description):
    db = get_db()
    now_utc = datetime.datetime.utcnow()
    db.execute(
        "INSERT INTO activity (user_id, action_type, description, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, action_type, description, now_utc)
    )
    db.commit()

# --- Main Routes ---
@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        error = None
        if not all([username, email, password, confirm_password]):
            error = 'All fields are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif username.lower() == 'admin':
            error = 'The username "admin" is reserved.'

        if error is None:
            db = get_db()
            if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone() is not None:
                error = f"Username '{username}' is already registered."
            elif db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone() is not None:
                error = f"Email address '{email}' is already in use."
            else:
                verification_code = str(random.randint(100000, 999999))
                code_expiry = datetime.datetime.utcnow() + timedelta(minutes=15)

                # --- MODIFIED: Use the new helper function ---
                email_sent = send_verification_email(email, username, verification_code)

                if email_sent:
                    db.execute(
                        "INSERT INTO users (username, email, password, verification_code, code_expiry) VALUES (?, ?, ?, ?, ?)",
                        (username, email, password, verification_code, code_expiry)
                    )
                    db.commit()
                    session['username_to_verify'] = username
                    flash('Registration successful! Please check your email for a verification code.', 'success')
                    return redirect(url_for('verify'))
                else:
                    error = "An error occurred. Could not send verification email. Please try again later."
        if error:
            flash(error, 'error')
    return render_template('register.html')

# ... (The rest of your routes: /verify, /login, /dashboard, etc., are unchanged) ...
# ... (Paste the rest of your unchanged routes here) ...
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if 'username_to_verify' not in session:
        flash('Your verification session has expired. Please register again.', 'warning')
        return redirect(url_for('register'))

    username = session['username_to_verify']
    if request.method == 'POST':
        submitted_code = request.form.get('code')
        error = None
        if not submitted_code or not submitted_code.isdigit() or len(submitted_code) != 6:
            error = "Please enter a valid 6-digit code."
        else:
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user is None:
                error = "An unexpected error occurred. Please register again."
            elif user['is_verified']:
                flash('Your account is already verified. Please log in.', 'info')
                session.pop('username_to_verify', None)
                return redirect(url_for('login'))
            elif user['code_expiry'] < datetime.datetime.utcnow():
                error = "Your verification code has expired. Please register again to get a new one."
            elif user['verification_code'] != submitted_code:
                error = "The verification code is incorrect. Please try again."
            else:
                try:
                    db.execute("UPDATE users SET is_verified = 1, verification_code = NULL, code_expiry = NULL WHERE username = ?", (username,))
                    db.commit()
                    flash('Your account has been successfully verified! You can now log in.', 'success')
                    session.pop('username_to_verify', None)
                    return redirect(url_for('login'))
                except sqlite3.Error as e:
                    error = "A database error occurred during verification. Please try again."
        if error:
            flash(error, 'error')
    return render_template('verify.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password_attempt = request.form['password']
        error = None
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user is None or user['password'] != password_attempt:
            error = 'Incorrect username or password.'
        elif not user['is_verified']:
            error = "Your account has not been verified. A new verification code has been sent."
            # Logic to resend code could be added here if desired
            session['username_to_verify'] = user['username']
            flash(error, 'warning')
            return redirect(url_for('verify'))

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            log_activity(user['id'], 'login', 'You logged in to StudyBuddy')
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash(error, 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()

    depts_with_counts = db.execute("SELECT department, COUNT(id) as note_count FROM notes GROUP BY department").fetchall()
    department_info = {
        'Computer Science Engineering': {'icon_class': 'fas fa-laptop-code'},
        'Electronics and Communication Engineering': {'icon_class': 'fas fa-microchip'},
        'Electrical and Electronics Engineering': {'icon_class': 'fas fa-bolt'},
        'Mechanical Engineering': {'icon_class': 'fas fa-cogs'},
        'Civil Engineering': {'icon_class': 'fas fa-hard-hat'}
    }
    departments = []
    for dept_name in department_info:
        count_row = next((d for d in depts_with_counts if d['department'] == dept_name), None)
        departments.append({
            'name': dept_name,
            'icon_class': department_info[dept_name]['icon_class'],
            'note_count': count_row['note_count'] if count_row else 0
        })

    activities_from_db = db.execute(
        "SELECT action_type, description, timestamp FROM activity WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5",
        (session['user_id'],)
    ).fetchall()

    recent_activity = []
    now_utc = datetime.datetime.utcnow()
    for act in activities_from_db:
        style_map = {'login': 'success', 'download': 'primary', 'upload': 'info'}
        icon_map = {'login': 'user-check', 'download': 'file-download', 'upload': 'file-upload'}
        recent_activity.append({
            'style_class': style_map.get(act['action_type'], 'secondary'),
            'icon': icon_map.get(act['action_type'], 'info-circle'),
            'description': act['description'],
            'time_ago': humanize.naturaltime(now_utc - act['timestamp'])
        })

    return render_template('dashboard.html', departments=departments, recent_activity=recent_activity)

@app.route('/department/<department_name>')
def show_department_years(department_name):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    years = db.execute("SELECT DISTINCT year FROM notes WHERE department = ? ORDER BY year ASC", (department_name,)).fetchall()
    total_notes = db.execute("SELECT COUNT(id) FROM notes WHERE department = ?", (department_name,)).fetchone()[0]
    pyq_count = db.execute("SELECT COUNT(id) FROM notes WHERE department = ? AND year = 5", (department_name,)).fetchone()[0]
    return render_template('department_years.html', department_name=department_name, years=years, total_notes=total_notes, pyq_count=pyq_count)

@app.route('/department/<department_name>/year/<int:year_num>')
def show_year_courses(department_name, year_num):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    courses = db.execute("SELECT course_name, COUNT(id) as note_count FROM notes WHERE department = ? AND year = ? GROUP BY course_name ORDER BY course_name ASC", (department_name, year_num)).fetchall()
    return render_template('year_courses.html', department_name=department_name, year_num=year_num, courses=courses)

@app.route('/department/<department_name>/year/<int:year_num>/course/<course_name>')
def show_course_notes(department_name, year_num, course_name):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    notes_from_db = db.execute(
        "SELECT id, title, uploaded_at, file_size FROM notes WHERE department = ? AND year = ? AND course_name = ? ORDER BY uploaded_at DESC",
        (department_name, year_num, course_name)
    ).fetchall()
    notes_for_template = []
    now_utc = datetime.datetime.utcnow()
    for note in notes_from_db:
        notes_for_template.append({
            'id': note['id'],
            'title': note['title'],
            'file_size': note['file_size'],
            'uploaded_at_raw': note['uploaded_at'].isoformat(),
            'time_ago': humanize.naturaltime(now_utc - note['uploaded_at'])
        })
    return render_template('course_notes.html', department_name=department_name, year_num=year_num, course_name=course_name, notes=notes_for_template)

@app.route('/download/<int:note_id>')
def download_note(note_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    note = db.execute("SELECT filename, title FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        flash('Note not found.', 'error')
        return redirect(url_for('dashboard'))
    try:
        log_activity(session['user_id'], 'download', f"You downloaded <strong>{note['title']}.pdf</strong>")
        return send_from_directory(app.config['UPLOAD_FOLDER'], note['filename'], as_attachment=True)
    except FileNotFoundError:
        flash('File not found on server. It may have been moved or deleted.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload_note():
    if not session.get('is_admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        title, department, year, course_name = request.form.get('title'), request.form.get('department'), request.form.get('year'), request.form.get('course_name')
        if not all([file, title, department, year, course_name]) or file.filename == '':
            flash('All fields and a file are required.', 'error')
            return redirect(request.url)
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                flash(f"File '{filename}' already exists. Please rename it.", 'error')
                return redirect(request.url)
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            db = get_db()
            try:
                now_utc = datetime.datetime.utcnow()
                db.execute(
                    "INSERT INTO notes (title, department, year, course_name, filename, file_size, uploader_id, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (title, department, int(year), course_name, filename, file_size, session['user_id'], now_utc)
                )
                db.commit()
                log_activity(session['user_id'], 'upload', f"You uploaded <strong>{title}.pdf</strong>")
                flash(f"Note '{title}' uploaded successfully!", 'success')
                return redirect(url_for('admin_upload_note'))
            except sqlite3.Error as e:
                flash(f"Database error: {e}", 'error')
                os.remove(file_path)
        else:
            flash('Invalid file type. Only PDF files are allowed.', 'error')
    return render_template('admin_upload.html')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)