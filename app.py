import os
import uuid
from flask import Flask, url_for, render_template, request, redirect, session, flash
import sqlite3
from moviepy.editor import VideoFileClip
from datetime import datetime
import pytz 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdfg12345'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def to_hkt(utc_dt_str):
    """A Jinja2 filter to convert a UTC datetime string to HKT."""
    if not utc_dt_str:
        return ""
    try:
        utc_dt_str_clean = utc_dt_str.split('.')[0]
        utc_dt = datetime.strptime(utc_dt_str_clean, '%Y-%m-%d %H:%M:%S')

        utc_zone = pytz.timezone('UTC')
        hkt_zone = pytz.timezone('Asia/Hong_Kong')

        hkt_dt = utc_zone.localize(utc_dt).astimezone(hkt_zone)

        return hkt_dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return utc_dt_str

app.jinja_env.filters['hkt'] = to_hkt


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():    
    """Render the home page with user's posts if logged in."""
    posts = []
    if 'account_id' in session:
        conn = get_db_connection()
        posts = conn.execute(
            'SELECT p.*, a.firstname, a.lastname FROM posts p JOIN accounts a ON p.user_id = a.id WHERE p.user_id = ? ORDER BY p.upload_timestamp DESC',
            (session['account_id'],)
        ).fetchall()
        conn.close()
            
    return render_template('index.html', posts=posts)



@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    if 'account_id' not in session:
        flash('Please log in to upload files.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        description = request.form['description']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            original_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{original_extension}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(filepath)

            media_type = 'video' if original_extension == 'mp4' else 'image'

            if media_type == 'video':
                try:
                    clip = VideoFileClip(filepath)
                    duration = clip.duration
                    clip.close()
                    if duration > 60:
                        os.remove(filepath) 
                        flash('Video is too long! Maximum 30 seconds allowed.')
                        return redirect(request.url)
                except Exception as e:
                    os.remove(filepath) 
                    flash(f'Could not process video file: {e}')
                    return redirect(request.url)

            conn = get_db_connection()
            conn.execute(
                'INSERT INTO posts (user_id, description, filename, media_type) VALUES (?, ?, ?, ?)',
                (session['account_id'], description, unique_filename, media_type)
            )
            conn.commit()
            conn.close()

            flash('File successfully uploaded!')
            return redirect(url_for('newpost'))
        else:
            flash('File type not allowed. Please upload JPG, PNG, or MP4.')
            return redirect(request.url)


    return render_template('newpost.html')


@app.route('/mypost', methods=['GET'])
def mypost():
    """Render the user's posts."""
    if 'account_id' not in session:
        flash('Please log in to view your posts.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    posts = conn.execute(
        'SELECT p.*, a.firstname, a.lastname FROM posts p JOIN accounts a ON p.user_id = a.id WHERE p.user_id = ? ORDER BY p.upload_timestamp DESC',
        (session['account_id'],)
    ).fetchall()
    conn.close()

    return render_template('mypost.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if not email or not password:
            flash('Email and password are required.')
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        account = conn.execute('SELECT * FROM accounts WHERE email = ? AND pd = ?', (email, password)).fetchone()
        conn.close()

        if account is None:
            flash('Invalid email or password.')
            return redirect(url_for('login'))
        
        session['account_id'] = account['id']
        session['first_name'] = account['firstname']
        session['last_name'] = account['lastname']
        session['email'] = account['email']
        session['password'] = account['pd']
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/profile/<first_name><last_name>')
def profile(first_name, last_name):
    """Render the profile page."""
    if 'account_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    return render_template('profile.html', first_name=first_name, last_name=last_name)


@app.route('/logout')
def logout():
    session.pop('account_id', None)
    session.pop('email', None)  
    session.clear()
    return redirect(url_for('index'))


    
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
        
        conn = get_db_connection()
        existing_email = conn.execute('SELECT id FROM accounts WHERE email = ?', (email,)).fetchone()

        if existing_email:
            flash('This email have been registered!')
            return redirect(url_for('register'))
        

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