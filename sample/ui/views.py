from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from .models import userdetails, studentcourse


# Create your views here.
def index(request):
    return render(request, 'index.html')

def log_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role') # This comes from the button clicked

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the role submitted matches the user's status
            if role == 'admin' and user.is_staff:
                auth_login(request, user)
                return redirect('admindashboard') # Redirect to admin dashboard URL
            elif role == 'student' and not user.is_staff:
                auth_login(request, user)
                return redirect('studentdashboard') # Redirect to student dashboard URL
            else:
                # User exists but is trying to log into the wrong portal
                messages.error(request, 'Invalid role for this account.')
                return redirect('login')
        else:
            # Invalid credentials
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    
    # For a GET request, just show the login page
    return render(request, 'login.html')

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
        
        if userdetails.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please login.")
            return redirect('login')
        
        if userdetails.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose another.")
            return render(request, 'register.html')
        
        reg = userdetails(
            username=username,
            fullname=fullname,
            email=email,
            password=password,
            confirmpassword=confirmpassword
        )
        reg.save()
        messages.success(request, "Registration Successfull! Please login.")
        return redirect('login')
    return render(request, 'register.html')

def userdashboard(request):
    return render(request, 'userdashboard.html')

def admindashboard(request):
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
    
    # For a GET request, fetch all courses and render the page
    all_courses = studentcourse.objects.all().order_by('-created_at')
    context = {'courses': all_courses}
    return render(request, 'admindashboard.html', context)


def logout_view(request):
    """
    Logs the user out and redirects them to the login page.
    """
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')