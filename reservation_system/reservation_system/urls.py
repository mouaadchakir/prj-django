"""
URL configuration for reservation_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from shows.views import (
    UserListView, UserCreateView,
    ShowListView, ShowCreateView, ShowDetailView, AdminShowListView,
    ReservationCreateView, PaymentPageView, PaymentView, PaymentErrorView,
    ShowUpdateView, ShowDeleteView, LoginView, profile_view, password_change_view,
    ticket_view, generate_demo_tickets, my_bookings, download_ticket_pdf
)

urlpatterns = [
    path('', ShowListView.as_view(), name='home'),
    path('accounts/register/', UserCreateView.as_view(), name='register'), 
    path('accounts/login/', LoginView.as_view(), name='login'), 
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'), 
    path('accounts/profile/', profile_view, name='profile'), 
    path('accounts/password_change/', password_change_view, name='password_change'), 

    # Payment URLs
    path('payment/<int:pk>/', PaymentPageView.as_view(), name='payment_page'),
    path('shows/<int:pk>/payment/', PaymentView.as_view(), name='payment'),
    
    # Admin URL
    path('admin/', admin.site.urls),
     
    # User URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),

    # Show URLs
    path('shows/', ShowListView.as_view(), name='show_list'),
    # ShowCreateView is now public, no login needed as per previous step
    path('shows/create/', ShowCreateView.as_view(), name='show_create'),
    path('shows/management/', AdminShowListView.as_view(), name='admin_show_list'), 
    path('shows/<int:pk>/', ShowDetailView.as_view(), name='show_detail'),
    path('shows/<int:pk>/update/', ShowUpdateView.as_view(), name='show_update'), 
    path('shows/<int:pk>/delete/', ShowDeleteView.as_view(), name='show_delete'), 
    path('shows/<int:pk>/reserve/', ReservationCreateView.as_view(), name='reservation_create'),

    # Ticket URLs
    path('my-bookings/', my_bookings, name='my_bookings'),
    path('tickets/<int:reservation_id>/', ticket_view, name='view_ticket'),
    path('tickets/<int:reservation_id>/download/', download_ticket_pdf, name='download_ticket'),
    path('generate-tickets/', generate_demo_tickets, name='generate_tickets'),

    # Django Auth URLs (logout, password change, etc.) are kept for now
    # If login is truly gone, LOGIN_URL in settings might need adjustment or handling
    #path('accounts/', include('django.contrib.auth.urls')), 
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
