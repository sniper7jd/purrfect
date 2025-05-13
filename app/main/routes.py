import os
from datetime import datetime, timezone
import requests
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app, abort, jsonify
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from langdetect import detect, LangDetectException
from werkzeug.utils import secure_filename
from app import db
from app.email import send_email
from app.main.forms import EditProfileForm, EmptyForm, PetForm, BlogPostForm, RSVPForm
from app.models import User, Pet, Message, BlogPost, Event, EventRSVP
from app.translate import translate
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET'])
@bp.route('/index')
@login_required
def index():
    search_query = request.args.get('search', '', type=str).strip().lower()
    sort_by = request.args.get('sort', '', type=str)
    species_filter = request.args.get('species', '', type=str)
    age_filter = request.args.get('age', '', type=str)
    page = request.args.get('page', 1, type=int)

    pets_query = Pet.query.filter_by(is_active=1)

    # Filter by search
    if search_query:
        pets_query = pets_query.filter(
            (Pet.name.ilike(f"%{search_query}%")) |
            (Pet.species.ilike(f"%{search_query}%"))
        )

    # Filter by species
    if species_filter:
        pets_query = pets_query.filter(Pet.species == species_filter)

    # Filter by age
    if age_filter == '0-2':
        pets_query = pets_query.filter(Pet.age <= 2)
    elif age_filter == '3-5':
        pets_query = pets_query.filter(Pet.age >= 3, Pet.age <= 5)
    elif age_filter == '6+':
        pets_query = pets_query.filter(Pet.age >= 6)

    # Sort
    if sort_by == 'alpha_asc':
        pets_query = pets_query.order_by(Pet.name.asc())
    elif sort_by == 'alpha_desc':
        pets_query = pets_query.order_by(Pet.name.desc())
    elif sort_by == 'location':
        pets_query = pets_query.order_by(Pet.location.asc())
    else:
        pets_query = pets_query.order_by(Pet.name.asc())  # default

    # Pagination
    pagination = pets_query.paginate(page=page, per_page=6, error_out=False)
    active_pets = pagination.items

    # Species filter options
    species_choices = sorted({pet.species for pet in Pet.query.distinct(Pet.species).all()})

    return render_template(
        'index.html',
        active_pets=active_pets,
        species_choices=species_choices,
        pagination=pagination
    )

@bp.route('/suggest')
@login_required
def suggest():
    query = request.args.get('query', '', type=str).lower()
    suggestions = []

    if query:
        pets = Pet.query.filter(
            (Pet.name.ilike(f"%{query}%")) |
            (Pet.species.ilike(f"%{query}%"))
        ).limit(10).all()

        seen = set()
        for pet in pets:
            if pet.name.lower().startswith(query) and pet.name not in seen:
                suggestions.append(pet.name)
                seen.add(pet.name)
            if pet.species.lower().startswith(query) and pet.species not in seen:
                suggestions.append(pet.species)
                seen.add(pet.species)

    return jsonify(suggestions)

@bp.route('/pet/<int:pet_id>')
def view_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)  # Fetch the pet by its ID
    return render_template('view_pet.html', pet=pet)

@bp.route('/like/<int:pet_id>', methods=['POST'])
@login_required
def like_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    current_user.like_pet(pet)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'liked'})
    return redirect(url_for('main.pet_detail', pet_id=pet_id))

@bp.route('/unlike/<int:pet_id>', methods=['POST'])
@login_required
def unlike_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    current_user.unlike_pet(pet)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'unliked'})
    return redirect(url_for('main.pet_detail', pet_id=pet_id))

@bp.route('/chat/<int:user_id>', methods=["GET", "POST"])
@login_required
def chat(user_id):
    user_self = current_user
    other_user = User.query.get(user_id)
    if other_user is None:
        return redirect(url_for('main.messages'))

    # Get all messages between the current user and the other user
    sent_messages = Message.query.filter_by(sender_id=user_self.id, receiver_id=other_user.id).all()
    received_messages = Message.query.filter_by(sender_id=other_user.id, receiver_id=user_self.id).all()
    messages = sorted(sent_messages + received_messages, key=lambda x: x.sent_at)

    if request.method == "POST":
        content = request.form['content'].strip()
        if content:
            message = Message(sender_id=user_self.id, receiver_id=other_user.id, content=content)
            db.session.add(message)
            db.session.commit()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True})

        return redirect(url_for('main.chat', user_id=other_user.id))

    return render_template('chat.html', user=other_user, messages=messages, user_self=user_self)

@bp.route('/chat/<int:user_id>/poll')
@login_required
def poll_messages(user_id):
    other_user = User.query.get(user_id)
    if not other_user:
        return jsonify({'error': 'User not found'}), 404

    sent_messages = Message.query.filter_by(sender_id=current_user.id, receiver_id=user_id)
    received_messages = Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id)
    all_messages = sent_messages.union(received_messages).order_by(Message.sent_at.asc()).all()

    return jsonify([
        {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_username': msg.sender.username,
            'receiver_id': msg.receiver_id,
            'content': msg.content,
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
            'me': msg.sender_id == current_user.id
        }
        for msg in all_messages
    ])

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


# Route to display all blog posts
@bp.route('/blog')
def blog():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('blog.html', posts=posts)

# Route to create a new blog post
@bp.route('/create_post', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in to create a post
def create_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        # Create a new blog post instance
        new_post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            author=current_user,  # Set the current user as the author
            date_posted=datetime.now()
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('main.blog'))  # Redirect to blog post listing
    return render_template('create_post.html', form=form)

@bp.route('/events')
def events():
    # Fetch all events from the database
    events_data = Event.query.all()

    # Get the RSVPs for the current user
    user_rsvps = {rsvp.event_id: rsvp for rsvp in EventRSVP.query.filter_by(user_id=current_user.id).all()}

    # Create an RSVP form for each event
    forms = {event.id: RSVPForm() for event in events_data}

    # Render the events page with the event data, forms, and user RSVPs
    return render_template('events.html', events=events_data, forms=forms, user_rsvps=user_rsvps)


@bp.route('/rsvp/<int:event_id>', methods=['POST'])
def rsvp(event_id):
    form = RSVPForm()

    if form.validate_on_submit():
        # Fetch the event from the database
        event = Event.query.get(event_id)

        if event:  # Ensure the event exists in the database
            # Check if the user already has an RSVP for this event
            user_rsvp = EventRSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first()

            if user_rsvp:
                # Update the existing RSVP if one exists
                user_rsvp.response = form.response.data
            else:
                # Create a new RSVP if the user hasn't responded yet
                new_rsvp = EventRSVP(
                    user_id=current_user.id,
                    event_id=event_id,
                    response=form.response.data
                )
                db.session.add(new_rsvp)

            db.session.commit()
            flash(f"You have successfully RSVP'd to the event {event.title}!", "success")

            # Send confirmation email if RSVP is 'yes'
            if form.response.data.lower() == 'yes':
                send_email(
                    _('[Event RSVP] Confirmation for your registration'),
                    sender=current_app.config['ADMINS'][0],
                    recipients=[current_user.email],
                    text_body=render_template('email/rsvp_confirmation.txt', user=current_user, event=event),
                    html_body=render_template('email/rsvp_confirmation.html', user=current_user, event=event)
                )
        else:
            flash("Event not found.", "danger")
    else:
        flash("RSVP failed. Please try again.", "danger")

    return redirect(url_for('main.events'))


@bp.route('/cancel_rsvp/<int:event_id>', methods=['POST'])
def cancel_rsvp(event_id):
    # Logic to cancel the RSVP for the current user
    rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=current_user.id).first()

    if rsvp:
        db.session.delete(rsvp)
        db.session.commit()
        flash("Your RSVP has been successfully cancelled.", "success")
    else:
        flash("RSVP not found.", "danger")

    return redirect(url_for('main.events'))


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    form = EmptyForm()
    return render_template('user.html', user=user, form=form)



@bp.route('/add_pet', methods=['GET', 'POST'])
@login_required
def add_pet():
    form = PetForm()
    if form.validate_on_submit():
        file = form.pet_picture.data
        picture_path = None

        if file and hasattr(file, 'filename') and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.root_path, 'static/pet_pics', filename)
            file.save(file_path)
            picture_path = f'pet_pics/{filename}'

        pet = Pet(
            name=form.name.data,
            species=form.species.data,
            age=form.age.data,
            bio=form.bio.data,
            interests=form.interests.data,
            is_active=form.is_active.data,
            location=form.location.data.title(),
            pet_picture=picture_path,
            owner=current_user
        )

        db.session.add(pet)
        db.session.commit()
        flash('Your pet has been added!', 'success')
        return redirect(url_for('main.user', username=current_user.username))

    return render_template('add_pet.html', form=form)


@bp.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    form = PetForm()

    if form.validate_on_submit():
        # Update pet attributes
        pet.name = form.name.data
        pet.species = form.species.data
        pet.age = form.age.data
        pet.bio = form.bio.data
        pet.interests = form.interests.data
        pet.is_active = form.is_active.data
        pet.location = form.location.data.title()

        # Handle pet picture upload
        file = form.pet_picture.data
        if file and hasattr(file, 'filename') and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.root_path, 'static/pet_pics', filename)
            file.save(file_path)
            pet.pet_picture = f'pet_pics/{filename}'

        db.session.commit()
        flash('Pet updated successfully!', 'success')
        return redirect(url_for('main.user', username=current_user.username))

    # Prepopulate the form with existing pet data for GET requests
    elif request.method == 'GET':
        form.name.data = pet.name
        form.species.data = pet.species
        form.age.data = pet.age
        form.bio.data = pet.bio
        form.interests.data = pet.interests
        form.is_active.data = pet.is_active
        form.location.data = pet.location  # Prepopulate location field

    return render_template('edit_pet.html', form=form, pet=pet)


@bp.route('/delete_pet/<int:pet_id>', methods=['POST'])
@login_required
def delete_pet(pet_id):
    pet = db.get_or_404(Pet, pet_id)
    if pet.owner != current_user:
        abort(403)

    db.session.delete(pet)
    db.session.commit()
    flash('Pet has been deleted.', 'success')
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data

        file = form.profile_picture.data
        if file and hasattr(file, 'filename') and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.root_path, 'static/profile_pics', filename)
            file.save(file_path)
            current_user.profile_picture = f'profile_pics/{filename}'

        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.user', username=current_user.username))

    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)



@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    data = request.get_json()
    return {'text': translate(data['text'],
                              data['source_language'],
                              data['dest_language'])}


