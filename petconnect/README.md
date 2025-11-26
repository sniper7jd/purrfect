# PetConnect - Social Network for Pets 🐾

A modern Instagram-like social platform for pets built with Django, PostgreSQL, and WebSockets.

## Features

### 📱 Instagram-like Feed
- **Posts**: Share photos with captions and hashtags
- **Stories**: 24-hour disappearing content
- **Likes & Comments**: Engage with content
- **Follow System**: Follow pets to see their posts

### 🐕 Enhanced Pet Profiles
- Detailed pet information (age, weight, gender, breed)
- Personality traits (energy level, temperament)
- Compatibility info (good with dogs/cats/kids)
- Health verification (vaccinations, microchip)
- Reviews from other users

### 💬 Real-time Messaging
- WebSocket-powered chat (Django Channels)
- Typing indicators
- Read receipts
- Instant message delivery

### 🔍 Smart Playdate Matching
- Filter by species, age, location
- Match by temperament and energy level
- Training level compatibility
- Map view for nearby pets

## Tech Stack

- **Backend**: Django 4.2+
- **Database**: PostgreSQL
- **Real-time**: Django Channels + WebSockets
- **Frontend**: Tailwind CSS
- **Server**: Daphne (ASGI)

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- pip

### Installation

1. **Clone and navigate**
```bash
cd petconnect
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create PostgreSQL database**
```bash
psql -U postgres
CREATE DATABASE petconnect;
\q
```

5. **Configure environment**
Create a `.env` file:
```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=petconnect
DB_USER=postgres
DB_PASSWORD=your-password
PLACES_API_KEY=your-google-api-key
```

6. **Run migrations**
```bash
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Run the server**
```bash
# Development (with WebSocket support)
python manage.py runserver

# Or with Daphne for full ASGI support
daphne petconnect.asgi:application
```

Visit `http://localhost:8000`

## Project Structure

```
petconnect/
├── accounts/          # User authentication
│   ├── models.py     # Custom User with verification
│   └── views.py      # Login, register, profile
├── pets/             # Pet profiles
│   ├── models.py     # Pet, Follow, Review
│   └── views.py      # Pet CRUD, follow/unfollow
├── feed/             # Social feed
│   ├── models.py     # Post, Story, Like, Comment
│   └── views.py      # Feed, posts, stories
├── chat/             # Real-time messaging
│   ├── consumers.py  # WebSocket consumer
│   └── routing.py    # WebSocket URLs
├── playdates/        # Discovery & matching
│   └── views.py      # Search, filters, map
├── templates/        # HTML templates
├── static/           # CSS, JS, images
└── petconnect/       # Project settings
    ├── settings.py   # Django config
    ├── asgi.py       # WebSocket config
    └── urls.py       # URL routing
```

## API Endpoints

### Feed
- `GET /` - Home feed
- `POST /post/create/` - Create post
- `POST /post/<id>/like/` - Like/unlike post
- `POST /post/<id>/comment/` - Add comment
- `POST /story/create/` - Create story

### Pets
- `GET /pets/<id>/` - Pet profile
- `POST /pets/<id>/follow/` - Follow pet
- `POST /pets/<id>/unfollow/` - Unfollow pet
- `GET /pets/add/` - Add pet form

### Chat (WebSocket)
- `ws://host/ws/chat/<conversation_id>/` - Real-time chat

### Playdates
- `GET /playdates/` - Discover pets
- `GET /playdates/match/` - Smart matching
- `GET /playdates/map/` - Map view

## Production Deployment

1. Set `DEBUG=False`
2. Use Redis for Channel Layers:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    }
}
```
3. Run with Daphne + Nginx
4. Configure SSL/TLS

## License

MIT License



