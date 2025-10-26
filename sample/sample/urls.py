"""
URL configuration for sample project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from ui import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.log_in, name="login"),
    path("register/", views.register, name="register"),
    path("userdashboard/", views.userdashboard, name="userdashboard"),
    path("admindashboard/", views.admindashboard, name="admindashboard"),
    path('logout/', views.logout_view, name='logout'),
    path('course/<int:course_id>/start-quiz/', views.start_ai_quiz, name='start_ai_quiz'),
    path('quiz/attempt/<int:quiz_id>/', views.take_ai_quiz, name='take_ai_quiz'),
]
