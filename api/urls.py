from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register', views.register_user),
    path('auth/login', views.login_user),
    path('auth/me', views.get_me),

    # Dashboard
    path('dashboard/stats', views.get_dashboard_stats),

    # Posts
    path('posts', views.PostListCreateView.as_view()),
    path('posts/<int:pk>', views.PostDetailView.as_view()),
    path('posts/slug/<str:slug>', views.get_post_by_slug),

    # Categories
    path('categories', views.CategoryListCreateView.as_view()),
    path('categories/<int:pk>', views.CategoryDetailView.as_view()),

    # Users
    path('users', views.UserListView.as_view()),
    path('users/<int:pk>', views.UserDetailView.as_view()),

    # Settings
    path('settings', views.SettingListCreateView.as_view()),

    # Contacts
    path('contacts', views.ContactListCreateView.as_view()),
    path('contacts/<int:pk>', views.ContactDetailView.as_view()),

    # Subscribers
    path('subscribers', views.SubscriberListCreateView.as_view()),
    path('subscribers/<int:pk>', views.SubscriberDetailView.as_view()),

    # Videos
    path('videos', views.VideoListCreateView.as_view()),
    path('videos/<int:pk>', views.VideoDetailView.as_view()),

    # EPapers
    path('epapers', views.EPaperListCreateView.as_view()),
    path('epapers/<int:pk>', views.EPaperDetailView.as_view()),
]
