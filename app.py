from flask import Flask, url_for, render_template, request, redirect, session, flash

# Configuration
# Initialize Flask application
app = Flask(__name__)


@app.route('/')
def index():    
    """Render the home page."""    
    return render_template('home.html')