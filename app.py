from flask import Flask, url_for, render_template, request, redirect, session, flash, abort

# Configuration
# Initialize Flask application
app = Flask(__name__)


@app.route('/')
def index():    
    """Render the home page."""    
    return render_template('home.html')

@app.route('/register')
def register():    
    """Render the home page."""    
    return render_template('register.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404