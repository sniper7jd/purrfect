from datetime import datetime, timezone

import requests
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app, abort, jsonify
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from langdetect import detect, LangDetectException
from app import db

from app.main.forms import EditProfileForm, EmptyForm, PostForm, PetForm, BlogPostForm
from app.models import User, Pet, Message
from app.translate import translate
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
    g.locale = str(get_locale())

@bp.route('/like/<int:pet_id>', methods=['POST'])
@login_required
def like_pet(pet_id):
    pet = db.session.get(Pet, pet_id)
    if pet is None:
        flash('Pet not found.', 'danger')
        return redirect(url_for('index'))

    current_user.like_pet(pet)
    flash('You liked the pet!', 'success')
    return redirect(request.referrer or url_for('index'))

@bp.route('/unlike/<int:pet_id>', methods=['POST'])
@login_required
def unlike_pet(pet_id):
    pet = db.session.get(Pet, pet_id)
    if pet is None:
        flash('Pet not found.', 'danger')
        return redirect(url_for('index'))

    current_user.unlike_pet(pet)
    flash('You unliked the pet.', 'info')
    return redirect(request.referrer or url_for('index'))

@bp.route('/chat/<int:user_id>', methods=["GET", "POST"])
@login_required
def chat(user_id):
    user = current_user
    other_user = User.query.get(user_id)

    if other_user is None:
        return redirect(url_for('main.messages'))  # Redirect if user not found

    # Get all messages between the current user and the other user
    sent_messages = Message.query.filter_by(sender_id=user.id, receiver_id=other_user.id).all()
    received_messages = Message.query.filter_by(sender_id=other_user.id, receiver_id=user.id).all()

    # Combine both lists and sort them by sent_at (ascending order)
    messages = sorted(sent_messages + received_messages, key=lambda x: x.sent_at)

    if request.method == "POST":
        content = request.form['content'].strip()  # Get the message content
        if content:  # Ensure message is not empty
            message = Message(sender_id=user.id, receiver_id=other_user.id, content=content)
            db.session.add(message)
            db.session.commit()

        # After sending the message, redirect to the same chat page to show the new message
        return redirect(url_for('main.chat', user_id=other_user.id))

    # Render the chat page with messages
    return render_template('chat.html', user=other_user, messages=messages)

@bp.route('/messages')
@login_required
def messages():
    user = current_user
    # Get the list of users the current user has messaged (either sent or received)
    sent_users = [msg.receiver for msg in user.sent_messages]
    received_users = [msg.sender for msg in user.received_messages]

    # Combine and remove duplicates
    users = set(sent_users + received_users)
    return render_template('message_list.html', users=users)

@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@login_required
def index():
    active_pets = Pet.query.filter_by(is_active=1).all()  # Fetch all active pets
    return render_template('index.html', active_pets=active_pets)

@bp.route('/blog')
def blog():
    return render_template('blog.html', title="Blog")

@bp.route('/events')
def events():
    return render_template('events.html', title="Events")

@bp.route('/adoption')
def adoption():
    return render_template('adoption.html', title="Adoption")

@bp.route('/pet/<int:pet_id>')
def view_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)  # Fetch the pet by its ID
    return render_template('view_pet.html', pet=pet)

@bp.route('/explore')
@login_required
def explore():

    return render_template('index.html', title='Home')


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    form = EmptyForm()
    return render_template('user.html', user=user, form=form)

@bp.route('/blog-post', methods=['GET', 'POST'])
def create_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        new_post = {
            'title': form.title.data,
            'content': form.content.data,
            'author': 'Anonymous',  # Replace with current_user if using login
            'date_posted': datetime.now()
        }
        posts.insert(0, new_post)
        return redirect(url_for('blog'))
    return render_template('create_post.html', form=form)


@bp.route('/add_pet', methods=['GET', 'POST'])
@login_required
def add_pet():
    form = PetForm()
    if form.validate_on_submit():
        pet = Pet(
            name=form.name.data,
            species=form.species.data,
            age=form.age.data,
            bio=form.bio.data,
            interests=form.interests.data,
            photo_url=form.photo_url.data,
            is_active=form.is_active.data,
            owner=current_user
        )
        db.session.add(pet)
        db.session.commit()
        flash('Your pet has been added!', 'success')
        return redirect(url_for('main.user', username=current_user.username))  # Adjust the redirect target as needed
    return render_template('add_pet.html', form=form)

@bp.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = db.get_or_404(Pet, pet_id)
    if pet.owner != current_user:
        abort(403)

    form = PetForm(obj=pet)
    if form.validate_on_submit():
        form.populate_obj(pet)
        db.session.commit()
        flash('Pet information updated!', 'success')
        return redirect(url_for('main.user', username=current_user.username))

    return render_template('edit_pet.html', form=form, pet=pet)



@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    data = request.get_json()
    return {'text': translate(data['text'],
                              data['source_language'],
                              data['dest_language'])}
