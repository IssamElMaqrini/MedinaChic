from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
import json

from accounts.forms import UserForm
from accounts.models import ShippingAddress, DeletedUser

User = get_user_model()
def signup(request):
    error_message = None
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                error_message = "Cette adresse email est déjà utilisée. Veuillez vous connecter ou utiliser une autre adresse."
            else:
                user = User.objects.create_user(email=email, password=password)
                login(request, user)
                return redirect('index')
        except IntegrityError:
            error_message = "Cette adresse email est déjà utilisée. Veuillez vous connecter ou utiliser une autre adresse."
    
    return render(request, 'accounts/signup.html', {'error_message': error_message})


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
    error_message = None
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                error_message = "Dit e-mailadres is al in gebruik. Log in of gebruik een ander e-mailadres."
            else:
                user = User.objects.create_user(email=email, password=password)
                login(request, user)
                return redirect('index-nl')
        except IntegrityError:
            error_message = "Dit e-mailadres is al in gebruik. Log in of gebruik een ander e-mailadres."
    
    return render(request, 'accounts/signup_nl.html', {'error_message': error_message})


@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get("password")
        user = authenticate(email=request.user.email, password=password)
        if user:
            # Sauvegarder les données de l'utilisateur avant suppression
            user_data = {
                'email': user.email,
                'date_joined': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            }
            DeletedUser.objects.create(
                email=user.email,
                deletion_reason="Demande de l'utilisateur",
                user_data=user_data
            )
            user.delete()
            messages.success(request, "Votre compte a été supprimé avec succès.")
            return redirect('index')
        else:
            messages.error(request, "Mot de passe incorrect. Impossible de supprimer le compte.")
            return redirect('profile')
    return redirect('profile')


@login_required
def delete_account_nl(request):
    if request.method == 'POST':
        password = request.POST.get("password")
        user = authenticate(email=request.user.email, password=password)
        if user:
            # Sauvegarder les données de l'utilisateur avant suppression
            user_data = {
                'email': user.email,
                'date_joined': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            }
            DeletedUser.objects.create(
                email=user.email,
                deletion_reason="Verzoek van de gebruiker",
                user_data=user_data
            )
            user.delete()
            messages.success(request, "Uw account is succesvol verwijderd.")
            return redirect('index-nl')
        else:
            messages.error(request, "Onjuist wachtwoord. Kan account niet verwijderen.")
            return redirect('profile-nl')
    return redirect('profile-nl')




