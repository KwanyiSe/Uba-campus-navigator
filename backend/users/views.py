from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('campus-map')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        auth_login(request, user)
        return redirect('campus-map')

    return render(request, 'accounts/register.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required(login_url='login')
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required(login_url='login')
def profile_edit_view(request):
    if request.method == 'POST':
       # TODO:
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'accounts/profile_edit.html', {'user': request.user323})
    