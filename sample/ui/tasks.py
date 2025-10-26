# ui/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import studentcourse, GeneratedQuiz
import requests
import json
from django.conf import settings
from django.utils import timezone

def generate_ai_notification_content(user_profile, course):
    # This function remains the same
    API_KEY = settings.GOOGLE_API_KEY
    if not API_KEY:
        print("Error: Google API Key not found.")
        return (f"Just a friendly reminder to continue your great work on the '{course.course_name}' course. "
                f"You're at {course.completion_percentage}% and so close to the finish line. Keep up the momentum!")

    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={API_KEY}"
    prompt = (
        f"Generate a short, friendly, and motivational email body for a student named {user_profile.fullname}. "
        f"The student needs to be reminded to complete their course: '{course.course_name}'. "
        f"They have already completed {course.completion_percentage}% of it. "
        f"Encourage them by highlighting how close they are to finishing. Keep it under 100 words."
    )
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_content = response.json()['candidates'][0]['content']['parts'][0]['text']
        return ai_content
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        print(f"Error calling Google AI API: {e}")
        return (f"Just a friendly reminder to continue your great work on the '{course.course_name}' course. "
                f"You're at {course.completion_percentage}% and so close to the finish line. Keep up the momentum!")


@shared_task
def send_daily_reminders():
    # This function remains the same
    users = User.objects.filter(is_active=True)
    for user in users:
        priority_course = studentcourse.objects.filter(student=user).exclude(status='Completed').order_by('-completion_percentage').first()
        if priority_course:
            email_body = generate_ai_notification_content(user.userprofile, priority_course)
            send_mail(
                f"A friendly reminder about your course: {priority_course.course_name}",
                email_body,
                'your.actual.email@gmail.com',  # Replace with your email
                [user.email],
                fail_silently=False,
            )


@shared_task
def send_ai_quiz_reminders():
    """
    Finds all active users and sends them one reminder for each uncompleted quiz they have.
    """
    # 1. Get all active users
    users = User.objects.filter(is_active=True)

    # 2. Loop through each user
    for user in users:
        # 3. Find all quizzes for this user that are not completed
        pending_quizzes = GeneratedQuiz.objects.filter(student=user, is_completed=False)

        # 4. Loop through their pending quizzes and send an email for each one
        for quiz in pending_quizzes:
            email_body = (f"Hi {user.userprofile.fullname},\n\n"
                          f"This is a friendly reminder to attempt the {quiz.difficulty} quiz for your course '{quiz.course.course_name}'.\n\n"
                          "Keep up your learning momentum!")

            send_mail(
                f"Reminder: Complete your {quiz.course.course_name} quiz!",
                email_body,
                'your.actual.email@gmail.com',  # Replace with your email
                [user.email],
                fail_silently=False,
            )