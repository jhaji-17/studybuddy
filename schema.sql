-- Remove tables if they already exist (useful for re-initializing during development)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

-- Create the 'users' table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each user, automatically increases
    username TEXT UNIQUE NOT NULL,        -- Username, must be unique and cannot be empty
    password_hash TEXT NOT NULL           -- Stores the HASHED password, cannot be empty
);

-- Create the 'notes' table
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each note
    title TEXT NOT NULL,                  -- Title of the note (e.g., "Calculus Chapter 1")
    year INTEGER NOT NULL,                -- Academic year (e.g., 1, 2, 3, 4)
    course_name TEXT NOT NULL,            -- Name of the course (e.g., "MA101 Calculus")
    filename TEXT NOT NULL,               -- The actual filename of the PDF stored on the server (e.g., "calculus_ch1_notes.pdf")
    uploader_id INTEGER,                  -- (Optional for now) Who uploaded it? Foreign key to users table
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- When the note was uploaded
    -- FOREIGN KEY (uploader_id) REFERENCES users (id) -- We can add this later if we implement multiple uploaders
);

-- Optional: You can add some initial data for testing if you want
-- For example, an admin user (we'll handle password hashing in Python later)
-- INSERT INTO users (username, password_hash) VALUES ('admin', 'temporary_placeholder_for_hashed_password');