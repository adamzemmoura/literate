import os
import enum
import requests

from flask import Flask, session, render_template, redirect, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.bootstrap import Bootstrap

app = Flask(__name__)

# set up Bootstrap
bootstrap = Bootstrap(app)

# Check for database environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Check for Goodreads API environment variable
if not os.getenv("GOODREADS_API_KEY"):
    raise RuntimeError("GOODREADS_API_KEY is not set")

GOODREADS_API_KEY = os.getenv("GOODREADS_API_KEY")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# forms imports db so import after db setup
from forms import SignUpForm, LoginForm, BookSearchForm, ReviewForm

# Keep track of the current search type (used to style search buttons correctly) by adding it to the session
class SearchType(enum.Enum):
    author = 1
    title = 2
    isbn = 3

# set secret key in app.config
app.config["SECRET_KEY"] = "you-will-never-guess-this"

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@app.route("/search/author", methods=['GET', 'POST'])
def search_author():
    # update search SearchType to author
    session['search_type'] = SearchType.author.name

    check_user_logged_in()

    form = BookSearchForm()
    search_results = None
    result_count = None

    if form.validate_on_submit():
        # query database using search text
        result_count = db.execute('SELECT COUNT(*) FROM books WHERE author LIKE :search_text', {'search_text': f"%{form.search_text.data.lower()}%" }).fetchall()
        search_results = db.execute('SELECT * FROM books WHERE author LIKE :search_text ORDER BY "title" ASC', {"search_text": f"%{form.search_text.data.lower()}%" }).fetchall()

        # results type is list of tuples, access the first element of the first tuple to get the result count
        result_count = result_count[0][0]

        # If there were no results, inform user via flashed message
        if result_count == 0:
            flash(f'Sorry, there was no results for {form.search_text.data}.')

    return render_template('index.html', title="Literate | Search", user=session.get('user_name'), form=form, search_results=search_results,
                            result_count=result_count, search_text=form.search_text.data, search_type=search_type.name))

@app.route('/search/title', methods=['GET', 'POST'])
def search_title():
    # update search SearchType to title
    session['search_type'] = SearchType.title.name

    check_user_logged_in()

    form = BookSearchForm()
    search_results = None
    result_count = None

    if form.validate_on_submit():
        # query database using search text
        result_count = db.execute('SELECT COUNT(*) FROM books WHERE title LIKE :search_text', {'search_text': f"%{form.search_text.data.lower()}%" }).fetchall()
        search_results = db.execute('SELECT * FROM books WHERE title LIKE :search_text ORDER BY title ASC', {'search_text': f"%{form.search_text.data.lower()}%" }).fetchall()

        # results type is list of tuples, access the first element of the first tuple to get the result count
        result_count = result_count[0][0]

        if result_count == 0:
            flash(f'Sorry, there was no results for {form.search_text.data}.')

    return render_template('index.html', user=session.get('user_name'), form=form, result_count=result_count, search_text=form.search_text.data,
                            search_results=search_results, search_type=session.get('search_type'))

@app.route('/search/isbn', methods=['GET', 'POST'])
def search_isbn():
    # update search SearchType
    session['search_type'] = SearchType.isbn.name

    check_user_logged_in()

    form = BookSearchForm()
    search_results = None
    result_count = None

    if form.validate_on_submit():
        result_count = db.execute('SELECT COUNT(*) FROM books WHERE isbn LIKE :search_text', {'search_text': f"%{form.search_text.data.lower()}%" }).fetchall()
        search_results = db.execute('SELECT * FROM books WHERE isbn LIKE :search_text ORDER BY title ASC', {'search_text': f"%{form.search_text.data.lower()}%" }).fetchall()

        # capitalize titles and authors in results
        for result in search_results:
            result.author.capitalize()
            result.title.capitalize()

        # results type is list of tuples, access the first element of the first tuple to get the result count
        result_count = result_count[0][0]

        if result_count == 0:
            flash(f'Sorry, there was no results for {form.search_text.data}.')

    return render_template('index.html', user=session.get('user_name'), form=form, result_count=result_count, search_results=search_results,
                            search_text=form.search_text.data, search_type=session.get('search_type'))

@app.route('/book/<string:isbn>', methods=['GET', 'POST'])
def book_detail(isbn):

    check_user_logged_in()
    user_id = session.get('user_id')

    # get the book review for the signed in user for the currently displayed book, if there is one.
    user_review_data = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND reviews.book_isbn = :isbn", {"user_id": user_id, "isbn": isbn}).fetchone()
    show_review_form = user_review_data is None

    # get all the reviews for the book
    reviews = db.execute('SELECT first_name, last_name, body, rating FROM users, reviews WHERE users.id = reviews.user_id AND reviews.book_isbn = :isbn', {"isbn": isbn}).fetchall()

    # create a review form, which will only be rendered if no review. Note: book_detail.html template has required logic.
    form = ReviewForm()

    if form.validate_on_submit() and user_review_data is None:
        db.execute("INSERT INTO reviews (book_isbn, body, rating, user_id) VALUES (:isbn, :body, :rating, :user_id)", {"isbn": isbn, "body": form.review_body.data, "rating": int(form.rating.data), "user_id": user_id})
        db.commit()
        flash(f'Review successfully uploaded.')
        return redirect(url_for('book_detail', isbn=isbn))

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn}).fetchone()

    if book is None:
        flash(f'Something went wrong whilst trying to display the book details. Please try again.')
        return redirect(url_for('search_author'))

    # get reviews from good reads API
    goodread_review_data = get_goodreads_book_reviews(isbn)['books'][0]
    review_count = "{:,}".format(goodread_review_data['work_reviews_count'])
    average_rating = goodread_review_data['average_rating']

    return render_template('book_detail.html', reviews=reviews, user_review_data=user_review_data, review_form=form,
                            book=book, show_review_form=show_review_form, user=session.get('user_name'), average_rating=average_rating, review_count=review_count)

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
        user = db.execute("SELECT * FROM users WHERE email = :email", {"email": form.email.data}).fetchone()
        flash(f'user: {user}')
        session['user_name'] = f'{user.first_name} {user.last_name}'
        session['user_id'] = f'{user.id}'
        return redirect(url_for('search_author'))
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
            session['user_name'] = user.first_name + ' ' + user.last_name
            session['user_id'] = user.id
            user_name = session.get('user_name')
            flash(f'Successfully logged in as {user_name}!')
            return redirect(url_for('search_author'))

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    # log user out of session and redirect to to login page
    user_name = session.get('user_name')
    session.pop('user_name', None)
    session.pop('user_id', None)
    flash(f'{user_name} logged out.')
    return redirect(url_for('login'))

@app.route('/api/book/<string:isbn>')
def api_book_details(isbn):

    book = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn}).fetchone()
    reviews = db.execute('SELECT first_name, last_name, body, rating FROM users, reviews WHERE users.id = reviews.user_id').fetchall()
    ratings_sum = db.execute("SELECT SUM(rating) FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()[0]

    review_count = 0

    if reviews is not None:
        review_count = len(reviews)

    if book is None:
        return jsonify({
            "error": 'Error : book with isbn {} could not be found.'.format(isbn),
        }), 404

    return jsonify({
        "author": book.author.capitalize(),
        "title": book.title.capitalize(),
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count,
        "average_score": ratings_sum / review_count,
    }), 200

def check_user_logged_in():
    # Check to see if the user is logged in already, redirect to login if not.
    if session.get('user_id') is None:
        return redirect(url_for('login'))

def get_goodreads_book_reviews(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                        params={"key": GOODREADS_API_KEY, "format": 'json', "isbns": isbn})
    return res.json()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
