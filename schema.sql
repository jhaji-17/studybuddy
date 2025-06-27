-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS activity;

-- User table with INSECURE plain text password and new columns for email verification
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,                      -- NEW: To store user's email
    password TEXT NOT NULL,                          -- Storing plain text passwords is NOT recommended
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    is_verified BOOLEAN NOT NULL DEFAULT 0,          -- NEW: Tracks if the user is verified (0=No, 1=Yes)
    verification_code TEXT,                          -- NEW: Stores the 6-digit code sent via email
    code_expiry TIMESTAMP                            -- NEW: Stores the time when the code becomes invalid
);

-- Notes table (This table remains unchanged)
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

-- Activity table (This table remains unchanged)
CREATE TABLE activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create a default admin user for initial setup.
-- This admin user is pre-verified.
-- IMPORTANT: The admin user needs a valid email, even if it's a placeholder.
INSERT INTO users (username, email, password, is_admin, is_verified) 
VALUES ('admin', 'admin@example.com', 'YourNewPasswordHere', 1, 1);