from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Inquiry, Booking, Category, Package, PackageType
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date
from django.core.exceptions import ValidationError

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]


class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
        required=False
    )
    gender = forms.ChoiceField(
        choices=[
            ("", "Select Gender"),
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        required=False,
    )
    photo = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = ["phone", "address", "date_of_birth", "gender", "photo"]

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            # Calculate age as of today (April 29, 2025)
            today = date(2025, 4, 29)
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise forms.ValidationError("You must be at least 16 years old.")
        return dob


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }


class BookingForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Booking
        fields = ["package", "start_date"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get user from kwargs
        super().__init__(*args, **kwargs)

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date:
            today = date(2025, 4, 29)  # Current date
            if start_date <= today:
                raise ValidationError("Start date must be in the future.")
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        package = cleaned_data.get("package")
        start_date = cleaned_data.get("start_date")

        if package and self.user:
            # Check for active bookings for the same package
            today = date(2025, 4, 29)
            active_bookings = Booking.objects.filter(
                user=self.user,
                package=package,
                end_date__gte=today
            )
            if active_bookings.exists():
                raise ValidationError(
                    f"You already have an active booking for {package.name} that has not expired."
                )

        return cleaned_data

    def save(self, commit=True, user=None):
        booking = super().save(commit=False)
        if user:
            booking.user = user

        # Calculate end date based on package duration
        package = booking.package
        booking.end_date = booking.start_date + timezone.timedelta(
            days=package.duration
        )

        if commit:
            booking.save()
        return booking


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match!")

        # Optional: Add password strength validation
        if new_password and len(new_password) < 8:
            raise forms.ValidationError("New password must be at least 8 characters long.")

        return cleaned_data 


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "id": "description", "rows": 4}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) < 3:
            raise forms.ValidationError("Category name must be at least 3 characters long.")
        return name
    

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ["name", "category", "package_type", "description", "duration", "price", "image", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "name"}),
            "category": forms.Select(attrs={"class": "form-control", "id": "category"}),
            "package_type": forms.Select(attrs={"class": "form-control", "id": "package_type"}),
            "description": forms.Textarea(attrs={"class": "form-control", "id": "description", "rows": 5}),
            "duration": forms.NumberInput(attrs={"class": "form-control", "id": "duration"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "id": "price", "step": "0.01"}),
            "image": forms.FileInput(attrs={"class": "form-control", "id": "image"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "is_active"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) < 3:
            raise forms.ValidationError("Package name must be at least 3 characters long.")
        return name

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_duration(self):
        duration = self.cleaned_data["duration"]
        if duration <= 0:
            raise forms.ValidationError("Duration must be a positive number.")
        return duration

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            if not image.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                raise forms.ValidationError("Only PNG, JPG, JPEG, or GIF images are allowed.")
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image size must not exceed 5MB.")
        return image
    
class PackageTypeForm(forms.ModelForm):
    class Meta:
        model = PackageType
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "id": "description", "rows": 4}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) < 3:
            raise forms.ValidationError("Package type name must be at least 3 characters long.")
        return name