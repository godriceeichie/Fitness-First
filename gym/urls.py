from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Guest User URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('packages/', views.packages, name='packages'),
    path('packages/<int:pk>/', views.package_detail, name='package_detail'),
    path('trainers/', views.trainers, name='trainers'),
    
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Registered User URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/<int:package_id>/', views.book_package, name='book_package'),
    path('bookings/', views.booking_history, name='booking_history'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-update-booking/<int:booking_id>/', views.admin_update_booking, name='admin_update_booking'),
    path('admin-packages/', views.admin_packages, name='admin_packages'),
    path('admin-add-package/', views.admin_add_package, name='admin_add_package'),
    path('admin-edit-package/<int:package_id>/', views.admin_edit_package, name='admin_edit_package'),
    path('admin-categories/', views.admin_categories, name='admin_categories'),
    path('admin-package-types/', views.admin_package_types, name='admin_package_types'),
    path('admin-reports/', views.admin_reports, name='admin_reports'),
    path('admin-inquiries/', views.admin_inquiries, name='admin_inquiries'),
    path('admin-trainers/', views.admin_trainers, name='admin_trainers'),
    path('admin-add-trainer/', views.admin_add_trainer, name='admin_add_trainer'),
]
