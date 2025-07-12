DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lastname last name TEXT NOT NULL,
    firstname first name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pd password NOT NULL
);