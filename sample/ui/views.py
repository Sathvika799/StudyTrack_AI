# ui/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .ai_service import generate_quiz_from_ai
from django.shortcuts import get_object_or_404

# UPDATED: Import UserProfile instead of userdetails
from .models import UserProfile, studentcourse, GeneratedQuiz, Question, Answer


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

    # Find a course with >= 75% completion that is not yet finished for the alert
    high_priority_course = studentcourse.objects.filter(
        student=request.user,
        completion_percentage__gte=75
    ).exclude(status='Completed').first()

    context = {
        'profile': profile,
        'ongoing_courses': ongoing_courses,
        'completed_courses': completed_courses,
        'high_priority_course': high_priority_course, # Add this to the context
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


@login_required
def start_ai_quiz(request, course_id):
    course = get_object_or_404(studentcourse, pk=course_id, student=request.user)
    
    # --- ADAPTIVE DIFFICULTY LOGIC ---
    last_quiz = GeneratedQuiz.objects.filter(course=course).order_by('-created_at').first()
    difficulty = 'Basic' # Default for the first quiz
    if last_quiz:
        if last_quiz.score is not None and last_quiz.score >= 75:
            # If the user scored well, increase the difficulty
            difficulty_levels = ['Basic', 'Intermediate', 'Advanced']
            current_index = difficulty_levels.index(last_quiz.difficulty)
            if current_index < len(difficulty_levels) - 1:
                difficulty = difficulty_levels[current_index + 1] # Go to next level
            else:
                difficulty = 'Advanced' # Stay at max level
        else:
            # Otherwise, keep the same difficulty
            difficulty = last_quiz.difficulty

    # --- GENERATE QUIZ AND SAVE TO DB ---
    quiz_questions = generate_quiz_from_ai(course.course_name, difficulty)
    
    if not quiz_questions:
        messages.error(request, "Sorry, the AI could not generate a quiz at this moment. Please try again later.")
        return redirect('userdashboard')

    # Create the main quiz record
    new_quiz = GeneratedQuiz.objects.create(student=request.user, course=course, difficulty=difficulty)
    
    # Save the questions and answers from the AI to our database
    for q_data in quiz_questions:
        question = Question.objects.create(quiz=new_quiz, text=q_data['text'])
        for i, ans_text in enumerate(q_data['answers']):
            Answer.objects.create(
                question=question,
                text=ans_text,
                is_correct=(i == q_data['correct_answer_index'])
            )
            
    return redirect('take_ai_quiz', quiz_id=new_quiz.id)


@login_required
def take_ai_quiz(request, quiz_id):
    quiz = get_object_or_404(GeneratedQuiz, pk=quiz_id, student=request.user)

    if request.method == 'POST':
        total_questions = quiz.questions.count()
        correct_answers = 0
        for question in quiz.questions.all():
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                correct_answer = question.answers.get(is_correct=True)
                if int(selected_answer_id) == correct_answer.id:
                    correct_answers += 1
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Update the quiz record with the score and mark as completed
        quiz.score = score
        quiz.is_completed = True
        quiz.save()
        
        messages.success(request, f"Quiz submitted! Your score is {score:.0f}%.")
        return redirect('userdashboard')

    context = {'quiz': quiz}
    # We can reuse the same quiz template structure
    return render(request, 'quiz.html', context)