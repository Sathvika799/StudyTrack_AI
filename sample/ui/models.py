# ui/models.py

from django.db import models
from django.contrib.auth.models import User # Import Django's built-in User model

# This is now a "profile" model. It adds extra fields to Django's User model.
class UserProfile(models.Model):
    # This creates a one-to-one link with Django's User model.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=100)
    
    # We no longer store username, email, or password here.
    # Django's User model handles that securely.

    def __str__(self):
        return self.user.username

class studentcourse(models.Model):
    # This creates a many-to-one link to a User.
    # One user can have many courses.
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
    
class Quiz(models.Model):
    course = models.ForeignKey(studentcourse, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} for {self.course.course_name}"

    def is_due_soon(self):
        # Returns true if the quiz is due within the next 2 days
        return timezone.now() <= self.due_date <= timezone.now() + timezone.timedelta(days=2)