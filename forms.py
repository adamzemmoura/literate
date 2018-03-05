from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from application import db

class SignUpForm(FlaskForm):
    first_name = StringField('First Name :', validators=[DataRequired()])
    last_name = StringField('Last Name :', validators=[DataRequired()])
    email = StringField('Email : ', validators=[DataRequired(), Email()])
    password = PasswordField('Password : ', validators=[DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm Password : ', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if db.execute("SELECT * FROM users WHERE email = :email", {'email': field.data}).fetchone():
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email : ', validators=[DataRequired(), Email()])
    password = PasswordField('Password : ', validators=[DataRequired()])
    submit = SubmitField('Log In')

class BookSearchForm(FlaskForm):
    search_text = StringField('Search by :', validators=[DataRequired()])
    submit = SubmitField('Search')

class ReviewForm(FlaskForm):
    review_body = TextAreaField('What did you think?', validators=[DataRequired()])
    rating = SelectField('Rating out of 5?', choices=[('5', '5'), ('4', '4'), ('3', '3'), ('2', '2'), ('1', '1')])
    submit = SubmitField('Submit')
