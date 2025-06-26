import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
# NO werkzeug.security imports are needed since we are doing plain text password comparison

app = Flask(__name__)
app.secret_key = 'your_real_unique_secret_key_generated_by_os_urandom' # Use your actual secret key
DATABASE = 'users.db'

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

# --- Routes ---
@app.route('/')
def home():
    if 'user_id' in session: # Check if user is already logged in
        return redirect(url_for('dashboard'))
    # If not logged in, show links to register/login
    return render_template('home.html') # We'll create home.html soon

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 6:
             error = 'Password must be at least 6 characters long.'
        elif password != confirm_password:
            error = 'Passwords do not match.'

        if error is None:
            db = get_db()
            try:
                existing_user = db.execute(
                    "SELECT id FROM users WHERE username = ?", (username,)
                ).fetchone()
                if existing_user:
                    error = f"User '{username}' is already registered."
                else:
                    db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, password), # Storing plain password
                    )
                    db.commit()
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('login'))
            except sqlite3.Error as e:
                error = f"Database error: {e}"
        
        if error:
            flash(error, 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password_attempt = request.form['password'] # Password user typed in login form
        error = None
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        # Direct plain text password comparison
        elif user['password_hash'] != password_attempt: # Comparing plain text with plain text
            error = 'Incorrect password.'

        if error is None:
            # Login successful, store user info in session
            session.clear() # Clear any old session data
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard')) # Redirect to the new dashboard page
        
        flash(error, 'error') # Show login error

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session: # Check if user is logged in
        # This is where the user will select year/course and see notes
        # For now, just a welcome message
        return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Dashboard</title></head>
            <body>
                <h1>Welcome to your Dashboard, {session['username']}!</h1>
                <p>Notes selection and download will be here.</p>
                <p><a href="{url_for('logout')}">Logout</a></p>
            </body>
            </html>
        """
    else: # If not logged in, redirect to login page
        flash('You need to be logged in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear() # Clear all session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('login')) # Redirect to login page after logout

if __name__ == '__main__':
    app.run(debug=True)