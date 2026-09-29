from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.forms import LoginForm, RegisterForm, UserProfileForm
from accounts.models import AuditLog

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log audit
            AuditLog.objects.create(
                user=user,
                action="User Login",
                target_model="CustomUser",
                target_id=str(user.id),
                details=f"Successful authentication for {user.username}."
            )
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password credentials.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def user_logout(request):
    if request.user.is_authenticated:
        AuditLog.objects.create(
            user=request.user,
            action="User Logout",
            target_model="CustomUser",
            target_id=str(request.user.id),
            details=f"User {request.user.username} signed out."
        )
        logout(request)
        messages.info(request, "You have been securely signed out.")
    return redirect('accounts:login')

def user_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            AuditLog.objects.create(
                user=user,
                action="User Registration",
                target_model="CustomUser",
                target_id=str(user.id),
                details=f"New user account registered for {user.username}."
            )
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

@login_required
def user_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action="Updated Profile",
                target_model="CustomUser",
                target_id=str(request.user.id),
                details="Updated profile attributes."
            )
            messages.success(request, "Your profile settings have been updated.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def audit_logs(request):
    if not (request.user.is_admin_user or request.user.is_superuser):
        messages.error(request, "Access restricted to Administrators.")
        return redirect('dashboard:index')

    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:100]
    return render(request, 'accounts/audit_logs.html', {'logs': logs})
