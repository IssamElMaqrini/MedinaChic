from django.contrib import admin
from .models import BlogPost, BlogComment, PrivateMessage, Conversation


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'title_nl', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__email']
    date_hierarchy = 'created_at'


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__email', 'recipient__email', 'content']
    date_hierarchy = 'created_at'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'last_message_at']
    search_fields = ['user1__email', 'user2__email']
    date_hierarchy = 'last_message_at'
