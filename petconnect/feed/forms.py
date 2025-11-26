"""Feed forms."""
from django import forms
from .models import Post, Comment, Story


class PostForm(forms.ModelForm):
    """Form for creating posts."""
    
    class Meta:
        model = Post
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'post-image-input',
            }),
            'caption': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none resize-none',
                'rows': 3,
                'placeholder': "Write a caption... Add hashtags to reach more people! #petlife",
            }),
        }


class CommentForm(forms.ModelForm):
    """Form for comments."""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'flex-1 px-4 py-2 border-0 outline-none bg-transparent',
                'placeholder': 'Add a comment...',
            }),
        }


class StoryForm(forms.ModelForm):
    """Form for creating stories."""
    
    class Meta:
        model = Story
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'story-image-input',
            }),
        }

