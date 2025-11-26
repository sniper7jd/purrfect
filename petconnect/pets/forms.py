"""Pet forms with required fields for comprehensive profiles."""
from django import forms
from .models import Pet, Review


class PetForm(forms.ModelForm):
    """Form for creating/editing pets with comprehensive required fields."""
    
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
                'required': True,
            }),
            'species': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'required': True,
            }, choices=[
                ('', 'Select species... *'),
                ('Dog', 'Dog'),
                ('Cat', 'Cat'),
                ('Rabbit', 'Rabbit'),
                ('Bird', 'Bird'),
                ('Fish', 'Fish'),
                ('Reptile', 'Reptile'),
                ('Hamster', 'Hamster'),
                ('Guinea Pig', 'Guinea Pig'),
                ('Other', 'Other'),
            ]),
            'breed': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'placeholder': 'e.g., Golden Retriever, Siamese',
                'required': True,
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'rows': 4,
                'placeholder': "Tell us about your pet's personality, favorite activities, and what makes them special! *",
                'required': True,
            }),
            'picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-brand file:text-white file:cursor-pointer',
                'accept': 'image/*',
            }),
            'age_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'min': 0,
                'max': 30,
                'placeholder': 'Years *',
                'required': True,
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
                'min': 0,
                'placeholder': 'Weight in lbs',
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'required': True,
            }),
            'energy_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'required': True,
            }),
            'temperament': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'required': True,
            }),
            'training_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'required': True,
            }),
            'social_preference': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'required': True,
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none',
                'placeholder': 'Start typing or use auto-detect... *',
                'id': 'location-input',
                'required': True,
                'autocomplete': 'off',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields required
        self.fields['name'].required = True
        self.fields['species'].required = True
        self.fields['breed'].required = True
        self.fields['bio'].required = True
        self.fields['age_years'].required = True
        self.fields['gender'].required = True
        self.fields['energy_level'].required = True
        self.fields['temperament'].required = True
        self.fields['training_level'].required = True
        self.fields['social_preference'].required = True
        self.fields['location'].required = True
        
        # Add empty choice for gender if not already there
        if not self.fields['gender'].choices[0][0] == '':
            self.fields['gender'].choices = [('', 'Select gender... *')] + list(self.fields['gender'].choices)
        
        # Add empty choice for temperament
        if not self.fields['temperament'].choices[0][0] == '':
            self.fields['temperament'].choices = [('', 'Select temperament... *')] + list(self.fields['temperament'].choices)


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
