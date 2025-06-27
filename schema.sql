-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS activity;

-- User table with INSECURE plain text password and admin flag
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL, -- Storing plain text passwords is NOT recommended
    is_admin BOOLEAN NOT NULL DEFAULT 0
);

-- Notes table with an explicit timestamp (no default)
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    year INTEGER NOT NULL,
    course_name TEXT NOT NULL,
    filename TEXT UNIQUE NOT NULL,
    file_size INTEGER NOT NULL,
    uploader_id INTEGER NOT NULL,
    uploaded_at TIMESTAMP NOT NULL,
    FOREIGN KEY (uploader_id) REFERENCES users (id)
);

-- Activity table with an explicit timestamp (no default)
CREATE TABLE activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

--
-- THIS IS THE NEW LINE YOU NEED TO ADD
-- Create a default admin user for initial setup. Password is 'admin'
--
INSERT INTO users (username, password, is_admin) VALUES ('admin', 'password', 1);