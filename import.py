import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():

    setup_database()

    f = open('books.csv')
    reader = csv.reader(f)
    next(reader)

    # title and author are lowercased to enable improved search results and string matching
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title.lower(), "author": author.lower(), "year": year})
        print(f"Added book : '{title}' by {author} \(isbn : {isbn}\)")

    db.commit()

def setup_database():
    db.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, first_name VARCHAR NOT NULL, last_name VARCHAR NOT NULL, email VARCHAR UNIQUE NOT NULL, password_hash VARCHAR NOT NULL);")
    db.execute("CREATE TABLE IF NOT EXISTS books (isbn VARCHAR UNIQUE PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL);")
    db.execute("CREATE TABLE IF NOT EXISTS reviews (id SERIAL PRIMARY KEY, book_isbn VARCHAR REFERENCES books, body TEXT NOT NULL, rating INTEGER NOT NULL, user_id INTEGER REFERENCES users);")

if __name__ == "__main__":
    main()
