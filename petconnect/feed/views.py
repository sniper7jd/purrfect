"""Feed views."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings

from pets.models import Pet, Follow
from .models import Post, PostLike, Comment, Story, StoryView
from .forms import PostForm, CommentForm, StoryForm


def home(request):
    """Instagram-like home feed."""
    if not request.user.is_authenticated:
        # Show landing page for non-authenticated users
        featured_pets = Pet.objects.filter(is_active=True).annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:6]
        return render(request, 'feed/landing.html', {'featured_pets': featured_pets})
    
    # Get pets the user follows
    following_pet_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('pet_id', flat=True)
    
    # Also include user's own pets
    own_pet_ids = request.user.pets.values_list('id', flat=True)
    all_pet_ids = list(following_pet_ids) + list(own_pet_ids)
    
    # Get posts from followed pets and own pets
    if all_pet_ids:
        posts = Post.objects.filter(pet_id__in=all_pet_ids).select_related('pet', 'pet__owner')
    else:
        # If not following anyone, show popular posts
        posts = Post.objects.annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count', '-created_at')[:20]
    
    # Get active stories from followed pets
    stories = Story.objects.filter(
        pet_id__in=all_pet_ids,
        expires_at__gt=timezone.now()
    ).select_related('pet').order_by('-created_at')
    
    # Group stories by pet
    stories_by_pet = {}
    for story in stories:
        if story.pet_id not in stories_by_pet:
            stories_by_pet[story.pet_id] = {
                'pet': story.pet,
                'stories': [],
                'has_unseen': False
            }
        stories_by_pet[story.pet_id]['stories'].append(story)
        # Check if user has seen this story
        if not StoryView.objects.filter(user=request.user, story=story).exists():
            stories_by_pet[story.pet_id]['has_unseen'] = True
    
    # Get user's liked posts for displaying like state
    user_liked_posts = set(
        PostLike.objects.filter(user=request.user).values_list('post_id', flat=True)
    )
    
    # Get user's pets for posting
    user_pets = request.user.pets.all()
    
    return render(request, 'feed/home.html', {
        'posts': posts,
        'stories_by_pet': stories_by_pet.values(),
        'user_liked_posts': user_liked_posts,
        'user_pets': user_pets,
    })


@login_required
def create_post(request):
    """Create a new post."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        pet_id = request.POST.get('pet_id')
        
        if not pet_id:
            return redirect('feed:create_post')
        
        pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)
        
        if form.is_valid():
            post = form.save(commit=False)
            post.pet = pet
            post.save()
            return redirect('feed:home')
    else:
        form = PostForm()
    
    user_pets = request.user.pets.all()
    if not user_pets:
        return redirect('pets:add')
    
    return render(request, 'feed/create_post.html', {
        'form': form,
        'user_pets': user_pets,
    })


@login_required
@require_POST
def like_post(request, post_id):
    """Like/unlike a post."""
    post = get_object_or_404(Post, pk=post_id)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': post.like_count
        })
    
    return redirect('feed:home')


@login_required
@require_POST
def add_comment(request, post_id):
    """Add comment to a post."""
    post = get_object_or_404(Post, pk=post_id)
    content = request.POST.get('content', '').strip()
    
    if content:
        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=content
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'username': comment.user.username,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat(),
                }
            })
    
    return redirect('feed:home')


@login_required
def create_story(request):
    """Create a new story."""
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        pet_id = request.POST.get('pet_id')
        
        pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)
        
        if form.is_valid():
            story = form.save(commit=False)
            story.pet = pet
            story.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('feed:home')
    
    return redirect('feed:home')


@login_required
def view_story(request, story_id):
    """View a story and mark as seen."""
    story = get_object_or_404(Story, pk=story_id)
    
    if story.is_active:
        StoryView.objects.get_or_create(user=request.user, story=story)
    
    # Get all active stories from this pet
    pet_stories = Story.objects.filter(
        pet=story.pet,
        expires_at__gt=timezone.now()
    ).order_by('created_at')
    
    return render(request, 'feed/view_story.html', {
        'story': story,
        'pet_stories': pet_stories,
    })


def post_detail(request, post_id):
    """View single post with comments."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related('user').all()
    
    user_liked = False
    if request.user.is_authenticated:
        user_liked = PostLike.objects.filter(user=request.user, post=post).exists()
    
    return render(request, 'feed/post_detail.html', {
        'post': post,
        'comments': comments,
        'user_liked': user_liked,
    })


@login_required
@require_POST
def delete_post(request, post_id):
    """Delete a post."""
    post = get_object_or_404(Post, pk=post_id, pet__owner=request.user)
    post.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('feed:home')



