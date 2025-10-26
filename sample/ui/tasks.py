# ui/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import studentcourse, Quiz
import requests # Make sure to run: pip install requests
from django.conf import settings
from django.utils import timezone

def generate_ai_notification_content(user_profile, course):
    API_URL = "https://api.openai.com/v1/chat/completions"
    API_KEY = settings.OPENAI_API_KEY

    prompt = (
        f"Generate a short, friendly, and motivational email body for a student named {user_profile.fullname}. "
        f"The student needs to be reminded to complete their course: '{course.course_name}'. "
        f"They have already completed {course.completion_percentage}% of it. "
        f"Encourage them by highlighting how close they are to finishing. Keep it under 100 words."
    )
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    # This payload structure depends on your AI provider (e.g., OpenAI, Google AI)
    payload = {
        "model": "gpt-3.5-turbo", # Example model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        # Adjust the next line based on the actual JSON response structure
        ai_content = response.json()['choices'][0]['message']['content']
        return ai_content
    except requests.exceptions.RequestException as e:
        print(f"Error calling AI API: {e}")
        # Fallback to a generic message if the AI fails
        return (f"Just a friendly reminder to continue your great work on the '{course.course_name}' course. "
                f"You're at {course.completion_percentage}% and so close to the finish line. Keep up the momentum!")


@shared_task
def send_daily_reminders():
    # Find all active users
    users = User.objects.filter(is_active=True)
    
    for user in users:
        # Find the best course to remind the user about:
        # One that is not complete and has the highest completion percentage.
        priority_course = studentcourse.objects.filter(
            student=user
        ).exclude(
            status='Completed'
        ).order_by('-completion_percentage').first()

        if priority_course:
            # Generate the personalized message using AI
            email_body = generate_ai_notification_content(user.userprofile, priority_course)
            
            send_mail(
                f"A friendly reminder about your course: {priority_course.course_name}",
                email_body,
                'your-email@gmail.com',  # From email
                [user.email],             # To email
                fail_silently=False,
            )

@shared_task
def send_quiz_reminders():
    # Find all quizzes that are due in the next 2 days and are not completed
    upcoming_quizzes = Quiz.objects.filter(completed=False, due_date__lte=timezone.now() + timezone.timedelta(days=2))

    for quiz in upcoming_quizzes:
        user = quiz.course.student
        email_body = (f"Hi {user.userprofile.fullname},\n\n"
                      f"This is a reminder that you have a quiz '{quiz.title}' for your course '{quiz.course.course_name}' "
                      f"due on {quiz.due_date.strftime('%B %d, %Y')}.\n\n"
                      "Good luck!")
        
        send_mail(
            f"Reminder: Quiz '{quiz.title}' is due soon!",
            email_body,
            'your-email@gmail.com',
            [user.email],
            fail_silently=False,
        )