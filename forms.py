from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class SignUpForm(FlaskForm):
    username = StringField('Username : ', validators=[DataRequired('Please enter a username')])
    password = PasswordField('Password : ', validators=[DataRequired('Please enter a password')])
    submit = SubmitField('Register')
