from django.db import models

# Create your models here.
class userdetails(models.Model):
    username=models.CharField(max_length=20)
    fullname=models.CharField(max_length=30)
    email=models.EmailField(max_length=30)
    password=models.CharField(max_length=16)
    confirmpassword=models.CharField(max_length=16)

class studentcourse(models.Model):
    student_name=models.CharField(max_length=30)
    course_name=models.CharField(max_length=30)
    start_date=models.DateField()
    end_date = models.DateField(null=True, blank=True)
    hours_spent = models.IntegerField(default=0)
    completion_percentage = models.IntegerField(default=0)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)