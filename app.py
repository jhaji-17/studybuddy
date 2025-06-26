import sqlite3
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, g, flash

app = Flask(__name__)
# Make sure to replace this with your own unique key
app.secret_key = 'your_real_unique_secret_key_generated_by_os_urandom'
DATABASE = 'users.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Database Helper Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Database Initialization Command ---
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('init-db')
def init_db_command():
    init_db()
    print('Initialized the database.')

# --- Helper function for file uploads ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        error = None
        if not username: error = 'Username is required.'
        elif not password: error = 'Password is required.'
        elif len(password) < 6: error = 'Password must be at least 6 characters long.'
        elif password != confirm_password: error = 'Passwords do not match.'
        if error is None:
            db = get_db()
            try:
                existing_user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
                if existing_user: error = f"User '{username}' is already registered."
                else:
                    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password))
                    db.commit()
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('login'))
            except sqlite3.Error as e: error = f"Database error: {e}"
        if error: flash(error, 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password_attempt = request.form['password']
        error = None
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None: error = 'Incorrect username.'
        elif user['password_hash'] != password_attempt: error = 'Incorrect password.'
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            if user['username'] == 'admin': session['is_admin'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash(error, 'error')
    return render_template('login.html')

# UPDATED Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to be logged in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    
    # This function just shows the main department selection page.
    return render_template('dashboard.html')

# NEW Placeholder Route for our Department logic
@app.route('/department/<department_name>')
# Find the old @app.route('/department/<department_name>') placeholder and REPLACE it with this:
@app.route('/department/<department_name>')
def show_department_years(department_name):
    if 'user_id' not in session:
        flash('You need to be logged in to access this page.', 'warning')
        return redirect(url_for('login'))

    db = get_db()
    # Find all distinct years for the selected department
    years_cursor = db.execute(
        "SELECT DISTINCT year FROM notes WHERE department = ? ORDER BY year ASC",
        (department_name,)
    )
    years = years_cursor.fetchall()

    return render_template('department_years.html', 
                           department_name=department_name, 
                           years=years)
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# UPDATED Admin Upload Route
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload_note():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part in the request.', 'error')
            return redirect(request.url)
        file = request.files['pdf_file']
        title = request.form['title']
        department = request.form['department']
        year = request.form['year']
        course_name = request.form['course_name']
        if file.filename == '':
            flash('No selected file.', 'error')
            return redirect(request.url)
        if not all([title, department, year, course_name]):
            flash('All fields (title, department, year, course) are required.', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                flash(f"File '{filename}' already exists. Please rename or upload a different file.", 'error')
                return redirect(request.url)
            file.save(file_path)
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO notes (title, department, year, course_name, filename, uploader_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, department, int(year), course_name, filename, session['user_id'])
                )
                db.commit()
                flash(f"Note '{title}' uploaded successfully!", 'success')
                return redirect(url_for('admin_upload_note'))
            except sqlite3.Error as e:
                flash(f"Database error while saving note metadata: {e}", 'error')
        else:
            flash('Invalid file type. Only PDF files are allowed.', 'error')
    return render_template('admin_upload.html')
# ADD THIS NEW PLACEHOLDER ROUTE FOR STEP 8
@app.route('/department/<department_name>/year/<int:year_num>')
def show_year_courses(department_name, year_num):
    # This is a placeholder for Step 8.
    return f"This will show courses for Department: {department_name}, Year: {year_num}"
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)