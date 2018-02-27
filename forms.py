from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class SignUpForm(FlaskForm):
    first_name = StringField('First Name :', validators=[DataRequired()])
    last_name = StringField('Last Name :', validators=[DataRequired()])
    email = StringField('Email : ', validators=[DataRequired()])
    password = PasswordField('Password : ', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email : ', validators=[DataRequired()])
    password = PasswordField('Password : ', validators=[DataRequired()])
    submit = SubmitField('Log In')
