from django.urls import path
from . import views

urlpatterns = [
    # Chat routes (FR) - MUST BE BEFORE blog routes to avoid slug conflict
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/send/', views.send_message, name='send_message'),
    path('chat/search/', views.user_search, name='user_search'),
    path('chat/<int:user_id>/', views.chat_conversation, name='chat_conversation'),
    
    # Blog routes (FR)
    path('', views.blog_list, name='blog_list'),
    path('create/', views.blog_create, name='blog_create'),
    path('article/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('article/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('article/<slug:slug>/delete/', views.blog_delete, name='blog_delete'),
    
    # Chat routes (NL) - MUST BE BEFORE blog routes to avoid slug conflict
    path('nl/chat/', views.chat_list_nl, name='chat_list_nl'),
    path('nl/chat/<int:user_id>/', views.chat_conversation_nl, name='chat_conversation_nl'),
    
    # Blog routes (NL)
    path('nl/', views.blog_list_nl, name='blog_list_nl'),
    path('nl/create/', views.blog_create_nl, name='blog_create_nl'),
    path('nl/article/<slug:slug>/', views.blog_detail_nl, name='blog_detail_nl'),
    path('nl/article/<slug:slug>/comment/', views.add_comment_nl, name='add_comment_nl'),
    path('nl/article/<slug:slug>/delete/', views.blog_delete_nl, name='blog_delete_nl'),
]
