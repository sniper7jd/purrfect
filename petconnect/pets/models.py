"""Enhanced Pet models with detailed profiles, follows, and reviews."""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse


class Pet(models.Model):
    """Enhanced Pet model with Instagram-like social features."""
    
    # Energy levels
    ENERGY_LOW = 'low'
    ENERGY_MEDIUM = 'medium'
    ENERGY_HIGH = 'high'
    ENERGY_CHOICES = [
        (ENERGY_LOW, 'Low'),
        (ENERGY_MEDIUM, 'Medium'),
        (ENERGY_HIGH, 'High ⚡️'),
    ]
    
    # Temperament options
    TEMPERAMENT_CHOICES = [
        ('calm', 'Calm & Gentle'),
        ('playful', 'Playful & Energetic'),
        ('friendly', 'Friendly & Social'),
        ('shy', 'Shy & Cautious'),
        ('independent', 'Independent'),
        ('protective', 'Protective'),
    ]
    
    # Gender options
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('male_neutered', 'Male, Neutered'),
        ('female_spayed', 'Female, Spayed'),
    ]
    
    # Training levels
    TRAINING_CHOICES = [
        ('none', 'No Formal Training'),
        ('basic', 'Basic Commands'),
        ('advanced', 'Advanced Training'),
        ('in_training', 'Currently In Training'),
    ]
    
    # Social comfort levels
    SOCIAL_CHOICES = [
        ('groups', 'Great in Groups'),
        ('one_on_one', 'Prefers One-on-One'),
        ('slow_intro', 'Needs Slow Introductions'),
        ('selective', 'Selective with Friends'),
    ]
    
    # Basic info
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)  # Dog, Cat, etc.
    breed = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    
    # Profile picture
    picture = models.ImageField(upload_to='pets/', blank=True, null=True)
    
    # Physical details
    age_years = models.PositiveIntegerField(default=0)
    age_months = models.PositiveIntegerField(default=0)
    weight_lbs = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    
    # Personality & behavior
    energy_level = models.CharField(max_length=10, choices=ENERGY_CHOICES, default=ENERGY_MEDIUM)
    temperament = models.CharField(max_length=20, choices=TEMPERAMENT_CHOICES, blank=True)
    training_level = models.CharField(max_length=20, choices=TRAINING_CHOICES, default='basic')
    social_preference = models.CharField(max_length=20, choices=SOCIAL_CHOICES, default='groups')
    
    # Compatibility
    good_with_dogs = models.BooleanField(default=True)
    good_with_cats = models.BooleanField(default=False)
    good_with_kids = models.BooleanField(default=True)
    good_with_strangers = models.BooleanField(default=True)
    
    # Health & safety verification
    vaccinations_current = models.BooleanField(default=False)
    microchipped = models.BooleanField(default=False)
    temperament_assessed = models.BooleanField(default=False)
    
    # Location
    location = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    place_id = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    available_for_playdate = models.BooleanField(default=True)
    available_for_sitting = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.breed or self.species})"

    def get_absolute_url(self):
        return reverse('pets:profile', kwargs={'pet_id': self.pk})

    @property
    def age_display(self):
        """Format age nicely."""
        if self.age_years > 0 and self.age_months > 0:
            return f"{self.age_years} yr {self.age_months} mo"
        elif self.age_years > 0:
            return f"{self.age_years} Year{'s' if self.age_years != 1 else ''}"
        else:
            return f"{self.age_months} Month{'s' if self.age_months != 1 else ''}"

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        """Pets this pet's owner follows."""
        return Follow.objects.filter(follower=self.owner).count()

    @property
    def post_count(self):
        return self.posts.count()

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return sum(r.rating for r in reviews) / len(reviews)

    @property
    def good_with_list(self):
        """Return list of what pet is good with."""
        items = []
        if self.good_with_dogs:
            items.append('Dogs')
        if self.good_with_cats:
            items.append('Cats')
        if self.good_with_kids:
            items.append('Kids')
        return items


class Follow(models.Model):
    """Follow relationship - users follow pets."""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'pet']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.pet.name}"


class Review(models.Model):
    """Reviews for pets from sitters, playdate partners, etc."""
    
    REVIEW_TYPE_CHOICES = [
        ('playdate', 'Playdate Partner'),
        ('sitter', 'Pet Sitter'),
        ('walker', 'Dog Walker'),
        ('other', 'Other'),
    ]
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES, default='playdate')
    rating = models.PositiveIntegerField(default=5)  # 1-5 stars
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.pet.name} by {self.reviewer.username}"



