import os

from flask import Flask, session, render_template, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from forms import SignUpForm

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# create some test data

# set secret key in app.config
app.config["SECRET_KEY"] = "you-will-never-guess-this"

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    # log user out of session
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    form = SignUpForm()
    return render_template('signup.html', title='Sign Up', form=form)

app.run(debug=True)
