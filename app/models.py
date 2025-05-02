from datetime import datetime, timezone
from hashlib import md5
from time import time
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    profile_picture: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    posts: so.Mapped[list['BlogPost']] = so.relationship('BlogPost', back_populates="author", lazy='dynamic')
    pets: so.Mapped[List["Pet"]] = so.relationship(back_populates="owner", cascade="all, delete-orphan")
    likes: so.Mapped[List["Like"]] = so.relationship(back_populates="user", cascade="all, delete-orphan")
    sent_messages: so.Mapped[List["Message"]] = so.relationship(
        foreign_keys='Message.sender_id', back_populates="sender", cascade="all, delete-orphan")
    received_messages: so.Mapped[List["Message"]] = so.relationship(
        foreign_keys='Message.receiver_id', back_populates="receiver", cascade="all, delete-orphan")
    event_rsvps: so.Mapped[List["EventRSVP"]] = so.relationship(
        back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)

    @property
    def liked_pets(self):
        return (
            db.session.query(Pet)
            .join(Like, Like.pet_id == Pet.id)
            .filter(Like.user_id == self.id)
            .all()
        )

    @property
    def liked_pets_query(self):
        return (
            db.session.query(Pet)
            .join(Like, Like.pet_id == Pet.id)
            .filter(Like.user_id == self.id)
        )

    def has_liked_pet(self, pet: "Pet") -> bool:
        return db.session.query(Like).filter_by(user_id=self.id, pet_id=pet.id).first() is not None

    def like_pet(self, pet: "Pet") -> None:
        if not self.has_liked_pet(pet):
            like = Like(user=self, pet=pet)
            db.session.add(like)
            db.session.commit()

    def unlike_pet(self, pet: "Pet") -> None:
        like = db.session.query(Like).filter_by(user_id=self.id, pet_id=pet.id).first()
        if like:
            db.session.delete(like)
            db.session.commit()

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Pet(db.Model):
    __tablename__ = 'pets'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'))
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    age: so.Mapped[Optional[int]] = so.mapped_column()
    species: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    bio: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    interests: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    location: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))
    pet_picture: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    is_active: so.Mapped[bool] = so.mapped_column(default=True)
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    owner: so.Mapped[User] = so.relationship(back_populates="pets")
    likes: so.Mapped[List["Like"]] = so.relationship(back_populates="pet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pet {self.name}>"




class Like(db.Model):
    __tablename__ = 'likes'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'))
    pet_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('pets.id', ondelete='CASCADE'))
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    user: so.Mapped[User] = so.relationship(back_populates="likes")
    pet: so.Mapped[Pet] = so.relationship(back_populates="likes")

    __table_args__ = (sa.UniqueConstraint('user_id', 'pet_id', name='unique_user_pet_like'),)

    def __repr__(self):
        return f"<Like user_id={self.user_id} pet_id={self.pet_id}>"



class Message(db.Model):
    __tablename__ = 'messages'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'))
    receiver_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'))
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    sent_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    sender: so.Mapped[User] = so.relationship(foreign_keys=[sender_id], back_populates="sent_messages")
    receiver: so.Mapped[User] = so.relationship(foreign_keys=[receiver_id], back_populates="received_messages")

    def __repr__(self):
        return f"<Message from={self.sender_id} to={self.receiver_id}>"

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(120), nullable=False)
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    author_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # Foreign key to User model
    date_posted: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow, nullable=False)

    # Relationships to User (author)
    author: so.Mapped[User] = so.relationship('User', back_populates="posts")

    def __repr__(self):
        return f"<BlogPost {self.title}>"


class Event(db.Model):
    __tablename__ = 'events'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    location: so.Mapped[Optional[str]] = so.mapped_column(sa.String(150))
    event_time: so.Mapped[datetime] = so.mapped_column(nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    rsvps: so.Mapped[List["EventRSVP"]] = so.relationship(back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event {self.title} at {self.event_time}>"

class EventRSVP(db.Model):
    __tablename__ = 'event_rsvps'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'))
    event_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('events.id', ondelete='CASCADE'))
    response: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False)  # 'yes' or 'no'
    responded_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    user: so.Mapped[User] = so.relationship(back_populates="event_rsvps")
    event: so.Mapped[Event] = so.relationship(back_populates="rsvps")

    __table_args__ = (sa.UniqueConstraint('user_id', 'event_id', name='unique_user_event_rsvp'),)

    def __repr__(self):
        return f"<RSVP user_id={self.user_id} event_id={self.event_id} response={self.response}>"

