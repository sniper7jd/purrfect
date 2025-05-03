from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.fields.choices import RadioField
from wtforms.fields.simple import BooleanField, FileField
from wtforms.validators import ValidationError, DataRequired, Length, Optional, URL, InputRequired
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from app import db
from app.models import User


class EditProfileForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired()])
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



class PetForm(FlaskForm):
    name = StringField('Pet Name', validators=[DataRequired()])
    species = StringField('Species', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[Optional()])
    interests = StringField('Interests', validators=[Optional()])
    location = StringField('Location', [DataRequired()])
    pet_picture = FileField("Pet Picture", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    is_active = BooleanField('Active?', default=True)
    submit = SubmitField('Add Pet')

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Post')


class RSVPForm(FlaskForm):
    response = RadioField(
        'RSVP',
        choices=[('yes', 'Yes'), ('no', 'No')],
        validators=[InputRequired()]
    )
    submit = SubmitField('Submit RSVP')

