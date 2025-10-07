# ui/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# UPDATED: Import UserProfile instead of userdetails
from .models import UserProfile, studentcourse


# Create your views here.
def index(request):
    return render(request, 'index.html')

def log_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if role == 'admin' and user.is_staff:
                auth_login(request, user)
                return redirect('admindashboard')
            elif role == 'student' and not user.is_staff:
                auth_login(request, user)
                return redirect('userdashboard')
            else:
                messages.error(request, 'Invalid role for this account.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    
    return render(request, 'login.html')

# === THIS ENTIRE FUNCTION IS NOW CORRECTED ===
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        fullname = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        confirmpassword = request.POST['confirmpassword']

        if password != confirmpassword:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html')
        
        # Check against Django's User model if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please login.")
            return redirect('login')
        
        # Check against Django's User model if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose another.")
            return render(request, 'register.html')
        
        # 1. Create the user with Django's secure method
        # This handles password hashing automatically.
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # 2. Create the linked UserProfile with the extra fullname field
        profile = UserProfile(user=user, fullname=fullname)
        profile.save()
        
        messages.success(request, "Registration Successful! Please login.")
        return redirect('login')
    
    return render(request, 'register.html')

@login_required
def userdashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    # Fetch courses that belong ONLY to the currently logged-in user (request.user)
    ongoing_courses = studentcourse.objects.filter(student=request.user).exclude(status='Completed').order_by('start_date')
    completed_courses = studentcourse.objects.filter(student=request.user, status='Completed').order_by('-end_date')

    # Put all the data into a context dictionary to send to the template
    context = {
        'profile': profile,
        'ongoing_courses': ongoing_courses,
        'completed_courses': completed_courses,
    }
    return render(request, 'userdashboard.html', context)

@login_required
def admindashboard(request):
    # This check ensures only admins can access the admin dashboard
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('login')

    if request.method == 'POST':
        student_username = request.POST.get('student_name')
        try:
            student_user = User.objects.get(username=student_username)
        except User.DoesNotExist:
            return JsonResponse({'message': f'Student "{student_username}" not found.'}, status=404)

        new_course = studentcourse(
            student=student_user,
            course_name=request.POST.get('course_name'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') or None,
            hours_spent=int(request.POST.get('hours_spent', 0)),
            completion_percentage=int(request.POST.get('completion_percentage', 0)),
            status=request.POST.get('status')
        )
        new_course.save()
        return JsonResponse({'message': 'Course saved successfully!'}, status=201)
    
    all_courses = studentcourse.objects.all().order_by('-created_at')
    context = {'courses': all_courses}
    return render(request, 'admindashboard.html', context)


def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')