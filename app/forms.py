from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email-Id', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Re-Enter the Password',
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email")


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[
                             DataRequired(), Length(min=10, max=140)])
    submit = SubmitField('Submit')

    def validate_username(self, username):
        user = User.query.filter_by(username=self.username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class PostForm(FlaskForm):
    post=TextAreaField('Say Something',validators=[DataRequired(),Length(max=140,min=10)])
    submit=SubmitField("Publish")

class ResetPasswordRequestForm(FlaskForm):
    email=StringField('email',validators=[DataRequired(),Email()])
    submit=SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password=PasswordField('New Password',validators=[DataRequired()])
    password2=PasswordField('Reenter the new password',validators=[EqualTo('password')])
    submit=SubmitField('Request Password Reset')


