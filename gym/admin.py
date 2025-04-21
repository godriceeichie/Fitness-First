from django.contrib import admin
from .models import Category, PackageType, Package, Trainer, Booking, Inquiry, UserProfile

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(PackageType)
class PackageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'package_type', 'price', 'duration', 'is_active')
    list_filter = ('category', 'package_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'experience', 'is_active')
    list_filter = ('is_active', 'specialization')
    search_fields = ('name', 'bio', 'specialization')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'start_date', 'end_date', 'status', 'payment_status', 'amount_paid')
    list_filter = ('status', 'payment_status')
    search_fields = ('user__username', 'package__name')
    date_hierarchy = 'created_at'

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)
    search_fields = ('name', 'email', 'message')
    date_hierarchy = 'created_at'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'gender')
    search_fields = ('user__username', 'user__email', 'phone')