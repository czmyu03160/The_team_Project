import os
import uuid
import random
from flask import Flask, url_for, render_template, request, redirect, session, flash
import sqlite3
from moviepy.editor import VideoFileClip
from datetime import datetime, timezone
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
    if not utc_dt_str:
        return ""
    try:
        utc_dt_str_clean = utc_dt_str.split('.')[0]
        utc_dt = datetime.strptime(utc_dt_str_clean, '%Y-%m-%d %H:%M:%S')

        utc_zone = pytz.timezone('UTC')
        hkt_zone = pytz.timezone('Asia/Hong_Kong')

        hkt_dt = utc_zone.localize(utc_dt).astimezone(hkt_zone)

        return hkt_dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return utc_dt_str

app.jinja_env.filters['hkt'] = to_hkt


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fetch_posts_with_comments(query, params=(), type_param=None):
    conn = get_db_connection()
    
    if 'ORDER BY' in query.upper():
        query = query.split('ORDER BY')[0].strip()
    
    if type_param:
        if 'WHERE' in query.upper():
            query += " AND p.type = ?"
        else:
            query += " WHERE p.type = ?"
        params = params + (type_param,)
    

    query += " ORDER BY p.upload_timestamp DESC"
    
    posts_from_db = conn.execute(query, params).fetchall()
    
    posts = [dict(row) for row in posts_from_db]

    for post in posts:
        comments = conn.execute(
            '''
            SELECT c.*, a.firstname 
            FROM comments c JOIN accounts a ON c.user_id = a.id 
            WHERE c.post_id = ? 
            ORDER BY c.created_at ASC
            ''', (post['id'],)
        ).fetchall()
        post['comments'] = comments 

    conn.close()
    return posts


@app.route('/')
def index():    
    query = 'SELECT p.*, a.firstname, a.lastname FROM posts p JOIN accounts a ON p.user_id = a.id'
    posts = fetch_posts_with_comments(query)
    carousel_posts = random.sample(posts, min(len(posts), 3)) if posts else []
    return render_template('index.html', posts=posts, carousel_posts=carousel_posts)


@app.route('/hobby') 
def hobby():    
    query = 'SELECT p.*, a.firstname, a.lastname FROM posts p JOIN accounts a ON p.user_id = a.id'
    posts = fetch_posts_with_comments(query, type_param='Hobby')  
    carousel_posts = random.sample(posts, min(len(posts), 3)) if posts else []
    return render_template('hobby.html', posts=posts, carousel_posts=carousel_posts)


@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'account_id' not in session:
        flash('You must be logged in to comment.')
        return redirect(url_for('login'))

    comment_text = request.form.get('comment_text')
    if not comment_text or not comment_text.strip():
        flash('Comment cannot be empty.')
        return redirect(request.referrer or url_for('index'))

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO comments (post_id, user_id, comment_text) VALUES (?, ?, ?)',
        (post_id, session['account_id'], comment_text)
    )
    conn.commit()
    conn.close()

    return redirect(request.referrer or url_for('index'))

@app.route('/update_comment/<int:comment_id>', methods=['GET', 'POST'])
def update_comment(comment_id):
    if 'account_id' not in session:
        flash('Please log in to edit comments.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()

    if comment is None:
        conn.close()
        flash('Comment not found.')
        return redirect(request.referrer or url_for('index'))

    if comment['user_id'] != session['account_id']:
        conn.close()
        flash('You are not authorized to edit this comment.')
        return redirect(request.referrer or url_for('index'))

    if request.method == 'POST':
        comment_text = request.form.get('comment_text')
        if not comment_text or not comment_text.strip():
            flash('Comment cannot be empty.')
            return render_template('update_comment.html', comment=comment)

        current_utc_time = datetime.now(timezone.utc)
        conn.execute(
            'UPDATE comments SET comment_text = ?, created_at = ? WHERE id = ?',
            (comment_text, current_utc_time, comment_id)
        )
        conn.commit()
        conn.close()
        flash('Comment updated successfully!')
        return redirect(request.form.get('redirect_url') or url_for('index'))

    conn.close()
    return render_template('update_comment.html', comment=comment, redirect_url=request.referrer)

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'account_id' not in session:
        flash('Please log in to delete comments.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()

    if comment is None:
        conn.close()
        flash('Comment not found.')
        return redirect(request.referrer or url_for('index'))

    if comment['user_id'] != session['account_id']:
        conn.close()
        flash('You are not authorized to delete this comment.')
        return redirect(request.referrer or url_for('index'))

    conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()

    flash('Comment deleted successfully.')
    return redirect(request.referrer or url_for('index'))


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
        post_type = request.form.get('type')  

        if not post_type:
            flash('Please select a type.')
            return redirect(request.url)

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
                'INSERT INTO posts (user_id, description, filename, media_type, type) VALUES (?, ?, ?, ?, ?)',  
                (session['account_id'], description, unique_filename, media_type, post_type)
            )
            conn.commit()
            conn.close()

            flash('File successfully uploaded!')
            return redirect(url_for('index'))
        else:
            flash('File type not allowed. Please upload JPG, PNG, or MP4.')
            return redirect(request.url)


    return render_template('newpost.html')


@app.route('/mypost', methods=['GET'])
def mypost():
    if 'account_id' not in session:
        flash('Please log in to view your posts.')
        return redirect(url_for('login'))

    query = 'SELECT p.*, a.firstname, a.lastname FROM posts p JOIN accounts a ON p.user_id = a.id WHERE p.user_id = ?'
    posts = fetch_posts_with_comments(query, (session['account_id'],)) 
    return render_template('mypost.html', posts=posts)


@app.route('/update_post/<int:post_id>', methods=['GET', 'POST'])
def update_post(post_id):
    if 'account_id' not in session:
        flash('Please log in to edit posts.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if post is None:
        conn.close()
        flash('Post not found.')
        return redirect(url_for('mypost'))

    if post['user_id'] != session['account_id']:
        conn.close()
        flash('You are not authorized to edit this post.')
        return redirect(url_for('mypost'))

    if request.method == 'POST':
        description = request.form['description']
        post_type = request.form['type']
        current_utc_time = datetime.now(timezone.utc)

        conn.execute(
            'UPDATE posts SET description = ?, type = ?, upload_timestamp = ? WHERE id = ?',
            (description, post_type, current_utc_time, post_id)
        )
        conn.commit()
        conn.close()
        
        flash('Post updated successfully!')
        return redirect(url_for('mypost'))

    conn.close()
    return render_template('update_post.html', post=post)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'account_id' not in session:
        flash('Please log in to delete posts.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if post is None:
        conn.close()
        flash('Post not found.')
        return redirect(url_for('mypost'))

    if post['user_id'] != session['account_id']:
        conn.close()
        flash('You are not authorized to delete this post.')
        return redirect(url_for('mypost'))

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], post['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        flash(f'Error deleting file: {e}')

    conn.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

    flash('Post deleted successfully.')
    return redirect(url_for('mypost'))

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


@app.route('/profile')
def profile():
    if 'account_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    return render_template('profile.html')


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'account_id' not in session:
        flash('Authentication required.')
        return redirect(url_for('login'))

    account_id = request.form.get('account_id')
    if str(session.get('account_id')) != account_id:
        flash('Unauthorized action.')
        return redirect(url_for('index'))

    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')

    if not all([first_name, last_name, email, password]):
        flash('All fields are required.')
        return redirect(url_for('profile'))

    conn = get_db_connection()
    existing_user = conn.execute('SELECT id FROM accounts WHERE email = ? AND id != ?', (email, account_id)).fetchone()
    if existing_user:
        flash('This email is already registered by another account.')
        conn.close()
        return redirect(url_for('profile'))

    conn.execute(
        'UPDATE accounts SET firstname = ?, lastname = ?, email = ?, pd = ? WHERE id = ?',
        (first_name, last_name, email, password, account_id)
    )
    conn.commit()
    conn.close()

    session['first_name'] = first_name
    session['last_name'] = last_name
    session['email'] = email
    session['password'] = password

    flash('Profile updated successfully!')
    return redirect(url_for('profile'))


@app.route('/logout')
def logout():
    session.pop('account_id', None)
    session.pop('email', None)  
    session.clear()
    return redirect(url_for('index'))

    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'account_id' in session:
        flash('You have logged-in.') 
        return redirect(url_for('index'))
    
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