-- Remove tables if they already exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

-- Create the 'users' table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Create the 'notes' table
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT NOT NULL,             -- <<-- NEW COLUMN
    year INTEGER NOT NULL,
    course_name TEXT NOT NULL,
    filename TEXT NOT NULL,
    uploader_id INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);