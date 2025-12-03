from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import BlogPost, BlogComment, PrivateMessage, Conversation
from django.contrib.auth import get_user_model

User = get_user_model()


# ============== BLOG VIEWS ==============

def blog_list(request):
    """Liste de tous les articles de blog (FR)"""
    posts = BlogPost.objects.filter(is_active=True).annotate(
        comment_count=Count('comments', filter=Q(comments__is_active=True))
    )
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )
    
    context = {
        'posts': posts,
        'search_query': search_query,
    }
    return render(request, 'blog/blog_list.html', context)


def blog_list_nl(request):
    """Liste de tous les articles de blog (NL)"""
    posts = BlogPost.objects.filter(is_active=True).annotate(
        comment_count=Count('comments', filter=Q(comments__is_active=True))
    )
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title_nl__icontains=search_query) | Q(content_nl__icontains=search_query) |
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )
    
    context = {
        'posts': posts,
        'search_query': search_query,
    }
    return render(request, 'blog/blog_list_nl.html', context)


def blog_detail(request, slug):
    """Détail d'un article avec ses commentaires (FR)"""
    post = get_object_or_404(BlogPost, slug=slug, is_active=True)
    comments = post.comments.filter(is_active=True)
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'blog/blog_detail.html', context)


def blog_detail_nl(request, slug):
    """Détail d'un article avec ses commentaires (NL)"""
    post = get_object_or_404(BlogPost, slug=slug, is_active=True)
    comments = post.comments.filter(is_active=True)
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'blog/blog_detail_nl.html', context)


@login_required
def blog_create(request):
    """Créer un nouvel article (FR)"""
    if request.method == 'POST':
        title = request.POST.get('title')
        title_nl = request.POST.get('title_nl')
        content = request.POST.get('content')
        content_nl = request.POST.get('content_nl')
        image = request.FILES.get('image')
        
        if title and content:
            post = BlogPost.objects.create(
                author=request.user,
                title=title,
                title_nl=title_nl,
                content=content,
                content_nl=content_nl,
                image=image
            )
            messages.success(request, "Votre article a été publié avec succès!")
            return redirect('blog_detail', slug=post.slug)
        else:
            messages.error(request, "Le titre et le contenu sont obligatoires.")
    
    return render(request, 'blog/blog_create.html')


@login_required
def blog_create_nl(request):
    """Créer un nouvel article (NL)"""
    if request.method == 'POST':
        title = request.POST.get('title')
        title_nl = request.POST.get('title_nl')
        content = request.POST.get('content')
        content_nl = request.POST.get('content_nl')
        image = request.FILES.get('image')
        
        if title and content:
            post = BlogPost.objects.create(
                author=request.user,
                title=title,
                title_nl=title_nl,
                content=content,
                content_nl=content_nl,
                image=image
            )
            messages.success(request, "Uw artikel is met succes gepubliceerd!")
            return redirect('blog_detail_nl', slug=post.slug)
        else:
            messages.error(request, "Titel en inhoud zijn verplicht.")
    
    return render(request, 'blog/blog_create_nl.html')


@login_required
def blog_delete(request, slug):
    """Supprimer un article (FR) - Seul l'auteur ou un admin peut supprimer"""
    post = get_object_or_404(BlogPost, slug=slug)
    
    # Vérifier les permissions : auteur ou admin
    if request.user == post.author or request.user.is_staff:
        if request.method == 'POST':
            post.delete()
            messages.success(request, "L'article a été supprimé avec succès.")
            return redirect('blog_list')
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer cet article.")
        return redirect('blog_detail', slug=slug)
    
    # Afficher la page de confirmation
    return render(request, 'blog/blog_confirm_delete.html', {'post': post})


@login_required
def add_comment(request, slug):
    """Ajouter un commentaire à un article (FR)"""
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, slug=slug, is_active=True)
        content = request.POST.get('content')
        
        if content:
            BlogComment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            messages.success(request, "Votre commentaire a été ajouté!")
        else:
            messages.error(request, "Le commentaire ne peut pas être vide.")
    
    return redirect('blog_detail', slug=slug)


@login_required
def blog_delete_nl(request, slug):
    """Supprimer un article (NL) - Seul l'auteur ou un admin peut supprimer"""
    post = get_object_or_404(BlogPost, slug=slug)
    
    # Vérifier les permissions : auteur ou admin
    if request.user == post.author or request.user.is_staff:
        if request.method == 'POST':
            post.delete()
            messages.success(request, "Het artikel is succesvol verwijderd.")
            return redirect('blog_list_nl')
    else:
        messages.error(request, "U heeft geen toestemming om dit artikel te verwijderen.")
        return redirect('blog_detail_nl', slug=slug)
    
    # Afficher la page de confirmation
    return render(request, 'blog/blog_confirm_delete_nl.html', {'post': post})


@login_required
def add_comment_nl(request, slug):
    """Ajouter un commentaire à un article (NL)"""
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, slug=slug, is_active=True)
        content = request.POST.get('content')
        
        if content:
            BlogComment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            messages.success(request, "Uw reactie is toegevoegd!")
        else:
            messages.error(request, "De reactie mag niet leeg zijn.")
    
    return redirect('blog_detail_nl', slug=slug)


@login_required
def delete_comment(request, comment_id):
    """Supprimer un commentaire (FR) - Admin ou auteur du commentaire"""
    comment = get_object_or_404(BlogComment, id=comment_id)
    post_slug = comment.post.slug
    
    # Vérifier les permissions : auteur du commentaire ou admin
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
        messages.success(request, "Le commentaire a été supprimé.")
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer ce commentaire.")
    
    return redirect('blog_detail', slug=post_slug)


@login_required
def delete_comment_nl(request, comment_id):
    """Supprimer un commentaire (NL) - Admin ou auteur du commentaire"""
    comment = get_object_or_404(BlogComment, id=comment_id)
    post_slug = comment.post.slug
    
    # Vérifier les permissions : auteur du commentaire ou admin
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
        messages.success(request, "De reactie is verwijderd.")
    else:
        messages.error(request, "U heeft geen toestemming om deze reactie te verwijderen.")
    
    return redirect('blog_detail_nl', slug=post_slug)


# ============== CHAT VIEWS ==============

@login_required
def chat_list(request):
    """Liste des conversations (FR)"""
    # Récupérer toutes les conversations de l'utilisateur
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    
    # Préparer les données pour chaque conversation
    conversation_data = []
    for conv in conversations:
        other_user = conv.user2 if conv.user1 == request.user else conv.user1
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(request.user)
        
        conversation_data.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    context = {
        'conversation_data': conversation_data,
    }
    return render(request, 'blog/chat_list.html', context)


@login_required
def chat_list_nl(request):
    """Liste des conversations (NL)"""
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    
    conversation_data = []
    for conv in conversations:
        other_user = conv.user2 if conv.user1 == request.user else conv.user1
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(request.user)
        
        conversation_data.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    context = {
        'conversation_data': conversation_data,
    }
    return render(request, 'blog/chat_list_nl.html', context)


@login_required
def chat_conversation(request, user_id):
    """Conversation avec un utilisateur spécifique (FR)"""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        messages.error(request, "Vous ne pouvez pas discuter avec vous-même!")
        return redirect('chat_list')
    
    # Récupérer ou créer la conversation
    conversation = Conversation.get_or_create_conversation(request.user, other_user)
    
    # Récupérer tous les messages
    chat_messages = conversation.get_messages()
    
    # Marquer les messages reçus comme lus
    PrivateMessage.objects.filter(
        recipient=request.user,
        sender=other_user,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'other_user': other_user,
        'conversation': conversation,
        'messages': chat_messages,
    }
    return render(request, 'blog/chat_conversation.html', context)


@login_required
def chat_conversation_nl(request, user_id):
    """Conversation avec un utilisateur spécifique (NL)"""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        messages.error(request, "U kunt niet met uzelf chatten!")
        return redirect('chat_list_nl')
    
    conversation = Conversation.get_or_create_conversation(request.user, other_user)
    chat_messages = conversation.get_messages()
    
    PrivateMessage.objects.filter(
        recipient=request.user,
        sender=other_user,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'other_user': other_user,
        'conversation': conversation,
        'messages': chat_messages,
    }
    return render(request, 'blog/chat_conversation_nl.html', context)


@login_required
def send_message(request):
    """Envoyer un message (AJAX)"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        
        if recipient_id and content:
            recipient = get_object_or_404(User, id=recipient_id)
            
            # Créer le message
            message = PrivateMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content
            )
            
            # Mettre à jour la conversation
            conversation = Conversation.get_or_create_conversation(request.user, recipient)
            conversation.save()  # Met à jour last_message_at
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'content': message.content,
                'created_at': message.created_at.strftime('%H:%M'),
            })
        
        return JsonResponse({'success': False, 'error': 'Données invalides'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def user_search(request):
    """Rechercher des utilisateurs pour démarrer une conversation (AJAX)"""
    query = request.GET.get('q', '')
    
    if query:
        users = User.objects.filter(
            Q(email__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        user_list = [{
            'id': user.id,
            'email': user.email,
        } for user in users]
        
        return JsonResponse({'success': True, 'users': user_list})
    
    return JsonResponse({'success': False, 'users': []})
