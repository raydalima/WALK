from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from admin_panel.models import Audience, CalendarEvent, PanelNotice
from .models import BlogPost, ImportantLink


def _visible_panel_q(user):
    if not getattr(user, 'is_authenticated', False):
        return Q(audience=Audience.TODOS)
    if user.is_admin_user():
        return Q()
    if user.is_teacher():
        return Q(audience__in=[Audience.TODOS, Audience.PROFESSORES])
    return Q(audience__in=[Audience.TODOS, Audience.ALUNOS])


def blog_list(request):
    """Lista de posts do blog"""
    posts = BlogPost.objects.filter(is_published=True).select_related('author')
    important_links = ImportantLink.objects.filter(is_active=True)
    featured_links = important_links.filter(is_featured=True)[:4]
    now = timezone.now()
    visible_q = _visible_panel_q(request.user)
    notices = (
        PanelNotice.objects.select_related('turma', 'created_by')
        .filter(visible_q, is_visible=True, published_at__lte=now)
        .order_by('-is_featured', '-published_at')[:6]
    )
    upcoming_events = (
        CalendarEvent.objects.select_related('turma', 'created_by')
        .filter(visible_q, is_visible=True, starts_at__gte=now)
        .order_by('starts_at')[:8]
    )
    
    # Filtro por categoria
    category = request.GET.get('category', '')
    if category:
        posts = posts.filter(category=category)

    posts = list(posts)
    carousel_posts = posts[:4]
    featured_post = posts[0] if posts and not category else None
    post_cards = posts[1:] if featured_post else posts
    
    context = {
        'posts': post_cards,
        'carousel_posts': carousel_posts,
        'featured_post': featured_post,
        'important_links': important_links,
        'featured_links': featured_links,
        'panel_notices': notices,
        'upcoming_events': upcoming_events,
        'category': category,
        'categories': BlogPost.Category.choices,
        'posts_count': len(posts),
    }
    return render(request, 'blog/blog_list.html', context)

def blog_detail(request, slug):
    """Detalhes de um post do blog"""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    
    # Incrementar visualizações
    post.increment_views()
    
    # Posts relacionados (mesma categoria)
    related_posts = BlogPost.objects.filter(
        category=post.category,
        is_published=True
    ).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    return render(request, 'blog/blog_detail.html', context)
