from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404

from accounts.forms import UserForm
from accounts.models import ShippingAddress

User = get_user_model()
def signup(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = User.objects.create_user(email=email, password=password)
        login(request, user)
        return redirect('index')
    return render(request, 'accounts/signup.html')


def login_user(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(email=email, password=password)
        if user:
            login(request, user)
            return redirect('index')

    return render(request, 'accounts/login.html')

def logout_user(request):
    logout(request)
    return redirect('index')

@login_required
def profile(request):
    if request.method == 'POST':
        is_valid = authenticate(email=request.POST.get("email"), password=request.POST.get("password"))
        if is_valid:
            user = request.user
            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.save()
        else:
            messages.add_message(request, messages.ERROR, "mot de passe incorrecte")

        return redirect("profile")

    form = UserForm(initial=model_to_dict(request.user, exclude="password"))
    addresses = request.user.addresses.all()

    return render(request, 'accounts/profile.html', context={'form': form,
                                                             "addresses": addresses})

@login_required
def set_default_shipping_address(request, pk):
    address: ShippingAddress = get_object_or_404(ShippingAddress, pk=pk)
    address.set_defaults()
    return redirect('profile')

@login_required
def delete_address(request, pk):
    address = get_object_or_404(ShippingAddress, pk=pk, user=request.user)
    address.delete()
    return redirect('profile')


@login_required
def profile_nl(request):
    if request.method == 'POST':
        is_valid = authenticate(email=request.POST.get("email"), password=request.POST.get("password"))
        if is_valid:
            user = request.user
            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.save()
        else:
            messages.add_message(request, messages.ERROR, "Onjuist wachtwoord")  # en néerlandais

        return redirect("profile-nl")

    form = UserForm(initial=model_to_dict(request.user, exclude="password"))
    addresses = request.user.addresses.all()

    return render(request, 'accounts/profile_nl.html', context={'form': form,
                                                                "addresses": addresses})


def login_user_nl(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(email=email, password=password)
        if user:
            login(request, user)
            return redirect('index-nl')  # redirection vers la page d'accueil NL

    return render(request, 'accounts/login_nl.html')


def logout_user_nl(request):
    logout(request)
    return redirect('index-nl')


def signup_nl(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = User.objects.create_user(email=email, password=password)
        login(request, user)
        return redirect('index-nl')  # Redirige vers la page d'accueil en néerlandais
    return render(request, 'accounts/signup_nl.html')
