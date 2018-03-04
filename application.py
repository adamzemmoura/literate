import os
import enum
import requests

from flask import Flask, session, render_template, redirect, url_for, flash, jsonify
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
GOODREADS_API_KEY = os.getenv("GOODREADS_API_KEY")
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# forms imports db so import after db setup
from forms import SignUpForm, LoginForm, BookSearchForm

class SearchType(enum.Enum):
    author = 1
    title = 2
    isbn = 3

# Keep track of the current search type (used to style search buttons correctly)
search_type = SearchType.author

# set secret key in app.config
app.config["SECRET_KEY"] = "you-will-never-guess-this"

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@app.route("/search/author", methods=['GET', 'POST'])
def search_author():
    # update search SearchType to author
    search_type = SearchType.author

    check_user_logged_in()

    form = BookSearchForm()
    search_results = None
    result_count = None

    if form.validate_on_submit():
        # query database using search text
        result_count = db.execute('SELECT COUNT(*) FROM books WHERE author LIKE :search_text', {'search_text': form.search_text.data }).fetchall()
        search_results = db.execute('SELECT * FROM books WHERE author LIKE :search_text ORDER BY title ASC', {'search_text': form.search_text.data }).fetchall()

        # results type is list of tuples, access the first element of the first tuple to get the result count
        result_count = result_count[0][0]

        # If there were no results, inform user via flashed message
        if result_count == 0:
            flash(f'Sorry, there was no results for {form.search_text.data}.')

    return render_template('index.html', user=session.get('user'), form=form, search_results=search_results,
                            result_count=result_count, search_text=form.search_text.data, search_type=search_type.name)

@app.route('/search/title', methods=['GET', 'POST'])
def search_title():
    # update search SearchType to title
    search_type = SearchType.title

    check_user_logged_in()

    form = BookSearchForm()
    search_results = None
    result_count = None

    if form.validate_on_submit():
        # query database using search text
        result_count = db.execute('SELECT COUNT(*) FROM books WHERE title LIKE :search_text', {'search_text': form.search_text.data }).fetchall()
        search_results = db.execute('SELECT * FROM books WHERE title LIKE :search_text ORDER BY title ASC', {'search_text': form.search_text.data }).fetchall()

        # results type is list of tuples, access the first element of the first tuple to get the result count
        result_count = result_count[0][0]

        if result_count == 0:
            flash(f'Sorry, there was no results for {form.search_text.data}.')

    return render_template('index.html', user=session.get('user'), form=form, result_count=result_count, search_text=form.search_text.data,
                            search_results=search_results, search_type=search_type.name)

@app.route('/search/isbn', methods=['GET', 'POST'])
def search_isbn():
    # update search SearchType
    search_type = SearchType.isbn

    check_user_logged_in()

    form = BookSearchForm()
    search_results = None
    result_count = None

    if form.validate_on_submit():
        result_count = db.execute('SELECT COUNT(*) FROM books WHERE isbn LIKE :search_text', {'search_text': form.search_text.data }).fetchall()
        search_results = db.execute('SELECT * FROM books WHERE isbn LIKE :search_text ORDER BY title ASC', {'search_text': form.search_text.data }).fetchall()

        # results type is list of tuples, access the first element of the first tuple to get the result count
        result_count = result_count[0][0]

        if result_count == 0:
            flash(f'Sorry, there was no results for {form.search_text.data}.')

    return render_template('index.html', user=session.get('user'), form=form, result_count=result_count, search_results=search_results,
                            search_text=form.search_text.data, search_type=search_type.name)

@app.route('/book/<string:isbn>')
def book_detail(isbn):

    check_user_logged_in()

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn}).fetchone()

    if book is None:
        flash(f'Something went wrong whilst trying to display the book details. Please try again.')
        return redirect(url_for('search_author'))

    # get reviews from good reads API
    goodread_reviews = get_goodreads_book_reviews(isbn)

    return render_template('book_detail.html', book=book, user=session.get('user'), goodread_reviews=goodread_reviews)

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    check_user_logged_in()

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

@app.route('/login', methods=['GET', 'POST'])
def login():

    check_user_logged_in()

    form = LoginForm()
    if form.validate_on_submit():
        # check to see if the user exists in the database
        user = db.execute("SELECT * FROM users WHERE email = :email", {'email': form.email.data}).fetchone()

        # if user doesn't exist or p/w wrong, flash a message to user and re-render login page
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password')
        else:
            # add user to session, flash login message and redirect to index.html (search_author)
            session['user'] = user.first_name + ' ' + user.last_name
            user = session.get('user')
            flash(f'Successfully logged in as {user}!')
            return redirect(url_for('search_author'))

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    # log user out of session and redirec to to login page
    session.pop('user', None)

    return redirect(url_for('login'))

@app.route('/api/book/<string:isbn>')
def api_book_details(isbn):

    book = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn}).fetchone()

    if book is None:
        return jsonify({
            "error": 'Error : invalid isbn.',
        }), 422

    return jsonify({
        "author": book.author,
        "title": book.title,
        "year": book.year,
        "isbn": book.isbn,
    }), 200

def check_user_logged_in():
    # Check to see if the user is logged in already, redirect to login if not.
    if session.get('user') is None:
        return redirect(url_for('login'))

def get_goodreads_book_reviews(isbn):
    res = requests.get("https://www.goodreads.com/book/isbn/",
                        params={"key": GOODREADS_API_KEY, "format": 'json', "isbn": isbn})
    return res.json()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
