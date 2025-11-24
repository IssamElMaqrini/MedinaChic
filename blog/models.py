from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from MedinaChic.settings import AUTH_USER_MODEL


class BlogPost(models.Model):
    """Article de blog posté par un utilisateur"""
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200, verbose_name="Titre")
    title_nl = models.CharField(max_length=200, blank=True, null=True, verbose_name="Titre (NL)")
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField(verbose_name="Contenu")
    content_nl = models.TextField(blank=True, null=True, verbose_name="Contenu (NL)")
    image = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Article de blog"
        verbose_name_plural = "Articles de blog"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # S'assurer que le slug est unique
            original_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_comments_count(self):
        return self.comments.filter(is_active=True).count()


class BlogComment(models.Model):
    """Commentaire sur un article de blog"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_comments')
    content = models.TextField(verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
    
    def __str__(self):
        return f"Commentaire de {self.author.email} sur {self.post.title}"


class PrivateMessage(models.Model):
    """Message privé entre deux utilisateurs"""
    sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Message privé"
        verbose_name_plural = "Messages privés"
    
    def __str__(self):
        return f"De {self.sender.email} à {self.recipient.email}"


class Conversation(models.Model):
    """Modèle pour regrouper les messages entre deux utilisateurs"""
    user1 = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_user1')
    user2 = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_user2')
    last_message_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        # Éviter les doublons (conversation A-B = B-A)
        unique_together = [['user1', 'user2']]
    
    def __str__(self):
        return f"Conversation entre {self.user1.email} et {self.user2.email}"
    
    def get_messages(self):
        """Récupère tous les messages de cette conversation"""
        return PrivateMessage.objects.filter(
            models.Q(sender=self.user1, recipient=self.user2) |
            models.Q(sender=self.user2, recipient=self.user1)
        ).order_by('created_at')
    
    def get_last_message(self):
        """Récupère le dernier message"""
        messages = self.get_messages()
        return messages.last() if messages.exists() else None
    
    def get_unread_count(self, user):
        """Nombre de messages non lus pour un utilisateur"""
        return PrivateMessage.objects.filter(
            recipient=user,
            is_read=False
        ).filter(
            models.Q(sender=self.user1) | models.Q(sender=self.user2)
        ).exclude(sender=user).count()
    
    @staticmethod
    def get_or_create_conversation(user1, user2):
        """Récupère ou crée une conversation entre deux utilisateurs"""
        # Toujours mettre le user avec le plus petit ID en premier pour éviter les doublons
        if user1.id > user2.id:
            user1, user2 = user2, user1
        
        conversation, created = Conversation.objects.get_or_create(
            user1=user1,
            user2=user2
        )
        return conversation
