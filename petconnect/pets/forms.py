"""Pet forms."""
from django import forms
from .models import Pet, Review


class PetForm(forms.ModelForm):
    """Form for creating/editing pets."""
    
    class Meta:
        model = Pet
        fields = [
            'name', 'species', 'breed', 'bio', 'picture',
            'age_years', 'age_months', 'weight_lbs', 'gender',
            'energy_level', 'temperament', 'training_level', 'social_preference',
            'good_with_dogs', 'good_with_cats', 'good_with_kids', 'good_with_strangers',
            'vaccinations_current', 'microchipped',
            'location', 'available_for_playdate', 'available_for_sitting',
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'placeholder': "Your pet's name",
            }),
            'species': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }, choices=[
                ('', 'Select species...'),
                ('Dog', 'Dog'),
                ('Cat', 'Cat'),
                ('Rabbit', 'Rabbit'),
                ('Bird', 'Bird'),
                ('Fish', 'Fish'),
                ('Reptile', 'Reptile'),
                ('Other', 'Other'),
            ]),
            'breed': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'placeholder': 'e.g., Golden Retriever, Siamese',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'rows': 4,
                'placeholder': "Tell us about your pet's personality, favorite activities, and what makes them special!",
            }),
            'picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'accept': 'image/*',
            }),
            'age_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'min': 0,
                'placeholder': 'Years',
            }),
            'age_months': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'min': 0,
                'max': 11,
                'placeholder': 'Months',
            }),
            'weight_lbs': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'step': '0.1',
                'placeholder': 'Weight in lbs',
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }),
            'energy_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }),
            'temperament': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }),
            'training_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }),
            'social_preference': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'placeholder': 'City, State',
                'id': 'location-input',
            }),
        }


class ReviewForm(forms.ModelForm):
    """Form for pet reviews."""
    
    class Meta:
        model = Review
        fields = ['review_type', 'rating', 'content']
        widgets = {
            'review_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'min': 1,
                'max': 5,
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'rows': 4,
                'placeholder': 'Share your experience with this pet...',
            }),
        }

