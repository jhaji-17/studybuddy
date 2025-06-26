import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
# REMOVE or comment out: from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_actual_secret_key_here' # MAKE SURE THIS IS SET TO SOMETHING REAL AND UNIQUE
DATABASE = 'users.db'

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

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("Database initialized with schema.sql!")

@app.cli.command('init-db')
def init_db_command():
    init_db()
    print('Initialized the database.')

@app.route('/')
def home():
    return """
        <h1>Welcome to the Notes Website!</h1>
        <p><a href="/register">Register</a></p>
        <p><a href="/login">Login</a></p>
    """

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] # Plain text password
        confirm_password = request.form['confirm_password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'

        if error is None:
            db = get_db()
            try:
                # Storing plain text password directly into the 'password_hash' column
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password), # Storing the plain 'password'
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))

        if error:
            flash(error, 'error')

    return render_template('register.html')

@app.route('/login') # Placeholder
def login():
    return "Login page placeholder. <a href='/register'>Go to Register</a> or <a href='/'>Home</a>"

if __name__ == '__main__':
    app.run(debug=True)