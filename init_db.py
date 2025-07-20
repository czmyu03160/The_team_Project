import sqlite3
connection = sqlite3.connect('database.db')
with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO accounts (lastname, firstname, email, pd) VALUES (?, ?, ?, ?)",
            ('Chen', 'Wei', 'wei.chen@example.com', 'password123')
            )
cur.execute("INSERT INTO accounts (lastname, firstname, email, pd) VALUES (?, ?, ?, ?)",
            ('Wang', 'Li', 'li.wang@example.com', 'securepass456')
            )

connection.commit()
connection.close()