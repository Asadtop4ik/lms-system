# lms/urls.py (app urls)
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # User Management - Superadmin
    path('admins/', views.admin_list, name='admin_list'),
    path('admins/create/', views.admin_create, name='admin_create'),

    # User Management - Admin
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),

    # Course Management
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('my-courses/', views.teacher_courses, name='teacher_courses'),
    path('courses/<int:course_id>/students/', views.course_students, name='course_students'),

    # Lesson Management
    path('courses/<int:course_id>/lesson/create/', views.lesson_create, name='lesson_create'),
    path('lessons/<int:lesson_id>/attendance/', views.mark_attendance, name='mark_attendance'),

    # Attendance Views
    path('my-attendance/', views.student_attendance, name='student_attendance'),

    # Student Enrollment
    path('enroll-student/', views.enroll_student, name='enroll_student'),
]