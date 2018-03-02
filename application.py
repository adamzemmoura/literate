import os

from flask import Flask, session, render_template, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, current_user, login_user, login_required
from flask.ext.bootstrap import Bootstrap

app = Flask(__name__)

# set up Bootstrap
bootstrap = Bootstrap(app)

# setup flask-login
login = LoginManager(app)
login.login_view = 'login'

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

# forms imports db so import after db setup
from forms import SignUpForm, LoginForm

# set secret key in app.config
app.config["SECRET_KEY"] = "you-will-never-guess-this"

@app.route("/")
@app.route("/index")
def index():
    if session.get('user') is None:
        return redirect(url_for('login'))
    return render_template('index.html', user=session.get('user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # check to see if the user is logged in already, redirect to index.html if so
    if session.get('user'):
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        # check to see if the user exists in the database
        user = db.execute("SELECT * FROM users WHERE email = :email", {'email': form.email.data}).fetchone()

        # if user doesn't exist or p/w wrong, flash a message to user and re-render login page
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password')
        else:
            # create a new User object using the user_data
            session['user'] = user.first_name + ' ' + user.last_name
            # log user in and redirect to index.html
            user = session.get('user')
            flash(f'Successfully logged in as {user}!')
            return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    # log user out of session
    session['user'] = None

    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if session.get('user'):
        return redirect(url_for('index'))

    form = SignUpForm()

    if form.validate_on_submit():
        password_hash = generate_password_hash(form.password.data)
        db.execute("INSERT INTO users (first_name, last_name, email, password_hash) VALUES (:first_name, :last_name, :email, :password_hash)",
            {"first_name": form.first_name.data, "last_name": form.last_name.data, "email": form.email.data, "password_hash": password_hash})
        db.commit()
        flash(f'{form.first_name.data} {form.last_name.data} is now registered')
        session['user'] = '{form.first_name.data} {form.last_name.data}'
        return redirect(url_for('index'))
    return render_template('signup.html', title='Sign Up', form=form, user=session.get('user'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
