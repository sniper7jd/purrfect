from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.fields.simple import BooleanField, FileField
from wtforms.validators import ValidationError, DataRequired, Length, Optional, URL
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from app import db
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))

class PetForm(FlaskForm):
    name = StringField('Pet Name', validators=[DataRequired()])
    species = StringField('Species', validators=[Optional()])
    age = IntegerField('Age', validators=[Optional()])
    bio = TextAreaField('Bio', validators=[Optional()])
    interests = StringField('Interests', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    pet_picture = FileField("Pet Picture", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    is_active = BooleanField('Active?', default=True)
    submit = SubmitField('Add Pet')

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class RSVPForm(FlaskForm):
    submit = SubmitField('RSVP')


events_data = [
{
'id': 1,
'image': 'dogs_playing.jpg',
'venue': 'Stewart Park',
'date': '29 March 2025',
'time': '12:30 pm'
},
{
'id': 2,
'image': 'dogs_playing.jpg',
'venue': 'Stewart Park',
'date': '29 March 2025',
'time': '12:30 pm'
},
{
'id': 3,
'image': 'dogs_playing.jpg',
'venue': 'Stewart Park',
'date': '29 March 2025',
'time': '12:30 pm'
}
]