"""User model with verification and profile features."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from hashlib import md5


class User(AbstractUser):
    """Enhanced User model for PetConnect."""
    
    # Profile info
    name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    
    # Verification status
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    id_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Stats
    member_since = models.DateTimeField(default=timezone.now)
    response_rate = models.PositiveIntegerField(default=0)  # percentage
    last_seen = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username

    def avatar(self, size=128):
        """Generate Gravatar URL."""
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    @property
    def pet_count(self):
        return self.pets.count()

    @property
    def follower_count(self):
        """Total followers across all pets."""
        return sum(pet.follower_count for pet in self.pets.all())



