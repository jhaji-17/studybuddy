-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS activity;

-- User table (Unchanged)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    verification_code TEXT,
    code_expiry TIMESTAMP
);

-- Notes table with CASCADE DELETE
-- Notes table with CASCADE DELETE
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    year INTEGER NOT NULL,
    course_name TEXT NOT NULL,
    google_drive_file_id TEXT NOT NULL, -- <<< ADD THIS LINE
    uploader_id INTEGER NOT NULL,
    uploaded_at TIMESTAMP NOT NULL,
    FOREIGN KEY (uploader_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Activity table with CASCADE DELETE
CREATE TABLE activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    -- THIS LINE IS MODIFIED
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

