from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ListingForm, ProfileForm, UserRegistrationForm
from .models import Listing


def home(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "")
    if query:
        listings = Listing.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        listings = Listing.objects.all()
    return render(request, "listings/home.html", {"listings": listings, "query": query})


def profile(request: HttpRequest, username: str) -> HttpResponse:
    user = get_object_or_404(User, username=username)
    listings = user.listings.all()
    return render(
        request, "listings/profile.html", {"profile_user": user, "listings": listings}
    )


def listing_detail(request: HttpRequest, pk: int) -> HttpResponse:
    listing = get_object_or_404(Listing, pk=pk)
    return render(request, "listings/listing_detail.html", {"listing": listing})


@login_required
def listing_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            return redirect("home")
    else:
        form = ListingForm()
    return render(request, "listings/listing_form.html", {"form": form})


@login_required
def listing_update(request: HttpRequest, pk: int) -> HttpResponse:
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = ListingForm(instance=listing)
    return render(request, "listings/listing_form.html", {"form": form})


@login_required
def listing_delete(request: HttpRequest, pk: int) -> HttpResponse:
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == "POST":
        listing.delete()
        return redirect("home")
    return render(request, "listings/listing_confirm_delete.html", {"listing": listing})


def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user_form.cleaned_data["password"])
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            return redirect("home")
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileForm()
    return render(
        request,
        "listings/register.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
def edit_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    if request.user != profile_user:
        messages.error(request, "You can only edit your own profile.")
        return redirect("profile", username=request.user.username)

    if request.method == "POST":
        profile = profile_user.profile
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile", username=profile_user.username)
    else:
        form = ProfileForm(instance=profile_user.profile)

    return render(
        request,
        "listings/profile_edit.html",
        {"form": form, "profile_user": profile_user},
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        password = request.POST.get("password")
        username = request.POST.get("username")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "listings/login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("home")
