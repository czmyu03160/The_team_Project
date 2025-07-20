DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS posts;

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lastname last name TEXT NOT NULL,
    firstname first name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pd password NOT NULL
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT,
    filename TEXT NOT NULL,
    media_type TEXT NOT NULL, 
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES accounts (id)
);