from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone

from .models import *
from .forms import *


# Guest User Views
def home(request):
    packages = Package.objects.filter(is_active=True)[
        :4
    ]  # Show only 4 featured packages
    trainers = Trainer.objects.filter(is_active=True)[
        :4
    ]  # Show only 4 featured trainers
    context = {
        "packages": packages,
        "trainers": trainers,
    }
    return render(request, "home.html", context)


def about(request):
    return render(request, "about.html")


def contact(request):
    if request.method == "POST":
        form = InquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your inquiry has been submitted successfully!")
            return redirect("contact")
    else:
        form = InquiryForm()

    return render(request, "contact.html", {"form": form})


def packages(request):
    categories = Category.objects.all()
    package_types = PackageType.objects.all()
    packages = Package.objects.filter(is_active=True)

    category_id = request.GET.get("category")
    package_type_id = request.GET.get("type")

    if category_id:
        packages = packages.filter(category_id=category_id)

    if package_type_id:
        packages = packages.filter(package_type_id=package_type_id)

    context = {
        "categories": categories,
        "package_types": package_types,
        "packages": packages,
    }
    return render(request, "gym/packages.html", context)


def package_detail(request, pk):
    package = get_object_or_404(Package, pk=pk, is_active=True)
    return render(request, "gym/package_detail.html", {"package": package})


def trainers(request):
    trainers = Trainer.objects.filter(is_active=True)
    return render(request, "gym/trainers.html", {"trainers": trainers})


# Auth Views
def register(request):
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            # Create an empty UserProfile instance for the user
            UserProfile.objects.create(user=user)
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserRegisterForm()

    context = {"user_form": user_form}
    return render(request, "registration/register.html", context)




# Registered User Views
@login_required
def dashboard(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-created_at")
    active_bookings = bookings.filter(
        status="confirmed", end_date__gte=timezone.now().date()
    )
    expired_bookings = bookings.filter(end_date__lt=timezone.now().date())

    context = {
        "bookings": bookings,
        "active_bookings": active_bookings,
        "expired_bookings": expired_bookings,
        "total_bookings": bookings.count(),
    }
    return render(request, "gym/dashboard.html", context)


@login_required
def book_package(request, package_id):
    package = get_object_or_404(Package, pk=package_id, is_active=True)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False, user=request.user)
            booking.save()

            messages.success(
                request, f"You have successfully booked the {package.name} package!"
            )
            return redirect("booking_history")
    else:
        form = BookingForm(initial={"package": package})

    return render(request, "gym/book_package.html", {"form": form, "package": package})


@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "gym/booking_history.html", {"bookings": bookings})


@login_required
def profile(request):
    try:
        user_profile = request.user.profile  # Access the user's UserProfile
    except UserProfile.DoesNotExist:
        # If UserProfile doesn't exist, create one
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

    context = {"user_form": user_form, "profile_form": profile_form}
    return render(request, "registration/profile.html", context)


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            current_password = form.cleaned_data.get("current_password")
            new_password = form.cleaned_data.get("new_password")

            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Your password was successfully updated!")
                return redirect("dashboard")
            else:
                messages.error(request, "Current password is incorrect!")
    else:
        form = PasswordChangeForm()

    return render(request, "registration/change_password.html", {"form": form})


# Admin Views (using is_staff flag)
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    total_users = User.objects.filter(is_staff=False).count()
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status="pending").count()
    total_revenue = (
        Booking.objects.filter(payment_status="full").aggregate(Sum("amount_paid"))[
            "amount_paid__sum"
        ]
        or 0
    )
    total_packages = Package.objects.count()  # Added
    pending_payments = Booking.objects.filter(
        payment_status__in=["pending", "partial"]
    ).count()  # Added

    recent_bookings = Booking.objects.all().order_by("-created_at")[:10]
    recent_users = User.objects.filter(is_staff=False).order_by("-date_joined")[:10]

    context = {
        "total_users": total_users,  # Maps to total_members in template
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,  # Maps to pending_payments in template
        "total_revenue": total_revenue,
        "total_packages": total_packages,  # New
        "recent_bookings": recent_bookings,
        "recent_users": recent_users,
    }
    return render(request, "admin/dashboard.html", context)


@login_required
def admin_bookings(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    status_filter = request.GET.get("status", "")
    payment_filter = request.GET.get("payment", "")

    bookings = Booking.objects.all().order_by("-created_at")

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    if payment_filter:
        bookings = bookings.filter(payment_status=payment_filter)

    context = {
        "bookings": bookings,
        "status_filter": status_filter,
        "payment_filter": payment_filter,
    }
    return render(request, "admin/bookings.html", context)


@login_required
def admin_update_booking(request, booking_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        status = request.POST.get("status")
        payment_status = request.POST.get("payment_status")
        amount_paid = request.POST.get("amount_paid")

        booking.status = status
        booking.payment_status = payment_status
        booking.amount_paid = amount_paid
        booking.save()

        messages.success(request, f"Booking #{booking.id} has been updated!")
        return redirect("admin_bookings")

    return render(request, "admin/update_booking.html", {"booking": booking})


@login_required
def admin_packages(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    packages = Package.objects.all().order_by("-created_at")
    return render(request, "admin/packages.html", {"packages": packages})


@login_required
def admin_categories(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    categories = Category.objects.all().order_by("name")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")

        category = Category(name=name, description=description)
        category.save()

        messages.success(request, f'Category "{name}" has been added!')
        return redirect("admin_categories")

    return render(request, "admin/categories.html", {"categories": categories})


@login_required
def admin_package_types(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    package_types = PackageType.objects.all().order_by("name")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")

        package_type = PackageType(name=name, description=description)
        package_type.save()

        messages.success(request, f'Package Type "{name}" has been added!')
        return redirect("admin_package_types")

    return render(request, "admin/package_types.html", {"package_types": package_types})


@login_required
def admin_add_package(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        package_type_id = request.POST.get("package_type")
        description = request.POST.get("description")
        duration = request.POST.get("duration")
        price = request.POST.get("price")
        is_active = "is_active" in request.POST

        category = get_object_or_404(Category, id=category_id)
        package_type = get_object_or_404(PackageType, id=package_type_id)

        package = Package(
            name=name,
            category=category,
            package_type=package_type,
            description=description,
            duration=duration,
            price=price,
            is_active=is_active,
        )

        if "image" in request.FILES:
            package.image = request.FILES["image"]

        package.save()

        messages.success(request, f'Package "{name}" has been added!')
        return redirect("admin_packages")

    categories = Category.objects.all()
    package_types = PackageType.objects.all()

    context = {
        "categories": categories,
        "package_types": package_types,
    }
    return render(request, "admin/add_package.html", context)


@login_required
def admin_edit_package(request, package_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    package = get_object_or_404(Package, id=package_id)

    if request.method == "POST":
        package.name = request.POST.get("name")
        package.category = get_object_or_404(Category, id=request.POST.get("category"))
        package.package_type = get_object_or_404(
            PackageType, id=request.POST.get("package_type")
        )
        package.description = request.POST.get("description")
        package.duration = request.POST.get("duration")
        package.price = request.POST.get("price")
        package.is_active = "is_active" in request.POST

        if "image" in request.FILES:
            package.image = request.FILES["image"]

        package.save()

        messages.success(request, f'Package "{package.name}" has been updated!')
        return redirect("admin_packages")

    categories = Category.objects.all()
    package_types = PackageType.objects.all()

    context = {
        "package": package,
        "categories": categories,
        "package_types": package_types,
    }
    return render(request, "admin/edit_package.html", context)


@login_required
def admin_reports(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    report_type = request.GET.get("type", "bookings")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    data = None

    if start_date and end_date:
        if report_type == "bookings":
            data = Booking.objects.filter(
                created_at__date__gte=start_date, created_at__date__lte=end_date
            ).order_by("-created_at")
        elif report_type == "users":
            data = User.objects.filter(
                date_joined__date__gte=start_date, date_joined__date__lte=end_date
            ).order_by("-date_joined")

    context = {
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "data": data,
    }
    return render(request, "admin/reports.html", context)


@login_required
def admin_inquiries(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    inquiries = Inquiry.objects.all().order_by("-created_at")
    return render(request, "admin/inquiries.html", {"inquiries": inquiries})


@login_required
def admin_trainers(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    trainers = Trainer.objects.all().order_by("name")
    return render(request, "admin/trainers.html", {"trainers": trainers})


@login_required
def admin_add_trainer(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page!")
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        specialization = request.POST.get("specialization")
        experience = request.POST.get("experience")
        bio = request.POST.get("bio")
        is_active = "is_active" in request.POST

        trainer = Trainer(
            name=name,
            specialization=specialization,
            experience=experience,
            bio=bio,
            is_active=is_active,
        )

        if "image" in request.FILES:
            trainer.image = request.FILES["image"]

        trainer.save()

        messages.success(request, f'Trainer "{name}" has been added!')
        return redirect("admin_trainers")

    return render(request, "admin/add_trainer.html")
