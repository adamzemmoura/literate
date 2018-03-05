# Project 1

Web Programming with Python and JavaScript

---
## Overview

For this project I built a book review site using Python and Flask as per the requirements below.  I named the app 'Literate' and it is now hosted on Heroku and can be viewed at (www.literate-app.com). The styling was achieved using Bootstrap via the flask-bootstrap package.

---
## Environment Variables

The following environment variables need to be set if running locally:

DATABASE_URL - containing the URL of the database
GOODREADS_API_KEY - containing the API key for the Goodreads api

The app checks that both environment variables are set, raising a RuntimeError if not.

---
## Requirements

1. **Registration: Users should be able to register for your website, providing (at minimum) a username and password.**

   If you are not currently logged in, any page attempted to be opened will redirect to the login view and render login.html.  Users are invited to log in but there is a link at the bottom - 'click here if you do not have an account' - for new users, which links to signup.html.  The user can then enter their first and last name, email and enter their password twice.  The registration form was built using the flask-wtf package.  All form fields are required and the passwords must match.  The registration form also has a custom validator, which checks that the user is not already registered ie. the email address is already in the database.  

2. **Login: Users, once registered, should be able to log in to your website with their username and password.**

   Once registered, users can login using their username and password by entering it on the login page. There is a sign in button on the top right of the navigation bar. Any time the user tries to navigate to a page, the app checks if a user is currently logged in and if not, redirects to the login page.  To log a user in, the email entered in the form is used to query the database.  The password entered is compared to the password hash for that user.  For security, the werkzeug-security package is used to for password hashing and checking.  If credentials are verified, the user's name and id are added to the session.     

3. **Logout: Logged in users should be able to log out of the site.**

   There is a logout button at the top right of the navigation bar.  If clicked, this logs the user out by removing the username and userid from the session.  Users are then redirected to the login page and a message is flashed to the top of the page to inform the user that the log out was successful.

4. **Import: Provided for you in this project is a file called books.csv, which is a spreadsheet in CSV format of 5000 different books. Each one has an ISBN nubmer, a title, an author, and a publication year. In a Python file called import.py separate from your web application, write a program that will take the books and import them into your PostgreSQL database. You will first need to decide what table(s) to create, what columns those tables should have, and how they should relate to one another. Run this program by running python3 import.py to import the books into your database, and submit this program with the rest of your project code.**

   The database was set up using the import.py file, which imports the books.csv file.  As per the requirement amendment, this file now also includes the required SQL commands to set up the tables if they don't already exist.

5. **Search: Once a user has logged in, they should be taken to a page where they can search for a book. Users should be able to type in the ISBN number of a book, the title of a book, or the author of a book. After performing the search, your website should display a list of possible matching results, or some sort of message if there were no matches. If the user typed in only part of a title, ISBN, or author name, your search page should find matches for those as well!**

   Once the user is logged in, they are redirected to the search page.  This consists of a wtf-form with three buttons used to select which parameter to use in search; author, title or isbn.  When clicked, a corresponding route and view is loaded.  A SearchType enum was created and stored to the session to allow the appropriate button to display in it's active state.  Title and author data was stored in lowercase to allow for better string matching and all SQL queries contain pre and post wildcards ie '%search_text%' to allow partial search text to match.  The results are displayed in a table, each with a 'reviews' button which links to the book detail page.

6. **Book Page: When users click on a book from the results of the search page, they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on your website**

   When users click on the review button from the search results table, the book_detail view renders book_detail.html, containing all the details of the book in; it's author, title, year and goodreads data if available. A breadcrumb navigation bar was added to allow easy navigation back to the search page.  The template is dynamic such that if the user has not yet entered a review for the currently displayed book, the book_review form will render (and won't if the user has already left a review).  All reviews for the book are displayed at the bottom of the page in a section titled Reviews.

7. **Review Submission: On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users should not be able to submit multiple reviews for the same book.**

    The form that renders if the user hasn't already entered a review accepts the text of review and a rating out of 5.  When submitted, a confirmation message flashes to the top of the app and the app is redirected to the book_detail view, which re-renders the book_detail page, this time without the ability to leave (another) review.

8. **Goodreads Review Data: On your book page, you should also display (if available) the average rating and number of ratings the work has received from Goodreads**

    The average rating and number of ratings is displayed in the top panel of the book_detail page.  If no data available, a message to that effect is displayed in it's place.  

9. **API Access: If users make a GET request to your website’s /api/<isbn> route, where <isbn> is an ISBN number, your website should return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score.**

    The API consists of the one required endpoint at /api/book/<isbn> The JSON response includes all the required data as per the requirement.  The review count and average score are the review and average score from this site (not goodreads). If the isbn is not in the database, the JSON response includes an message under the key of 'error' and returns a 404.

10. **Additional requirements**
    - Only used sqlalchemy with raw SQL commands throughout, not ORM.
    - Completed this README with write up.
    - requirements.txt was updated using pip freeze > requirements.txt
