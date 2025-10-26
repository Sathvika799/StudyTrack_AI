# ui/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- EXISTING MODELS ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=100)
    def __str__(self):
        return self.user.username

class studentcourse(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    hours_spent = models.IntegerField(default=0)
    completion_percentage = models.IntegerField(default=0)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.student.username} - {self.course_name}"

# --- NEW MODELS FOR AI-POWERED ADAPTIVE QUIZZES ---
class GeneratedQuiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('Basic', 'Basic'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(studentcourse, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Basic')
    score = models.FloatField(null=True, blank=True) # Score as a percentage
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Quiz for {self.course.course_name} by {self.student.username} ({self.difficulty})"

class Question(models.Model):
    # Now links to a specific quiz attempt
    quiz = models.ForeignKey(GeneratedQuiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=1000) # Increased length for complex questions

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text