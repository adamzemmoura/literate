from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
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
