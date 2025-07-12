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

@app.route('/register')
def register():       
    return render_template('register.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

__name__ = '__main__'
app.run(debug=True) 