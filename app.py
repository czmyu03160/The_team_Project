from flask import Flask, url_for, render_template, request, redirect, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
import sqlite3


app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdfg12345'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():    
    """Render the home page."""    
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        email = request.form['email']
        password = request.form['password']
        if not lastname or not firstname or not email or not password:
            flash('All fields are required.')
            return redirect(url_for('register'))
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO accounts (lastname, firstname, email, pd) VALUES (?, ?, ?, ?)',
                         (lastname, firstname, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('register.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

__name__ = '__main__'
app.run(debug=True) 