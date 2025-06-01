from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count, Avg
from .models import (
    User, Role, Course, Level, Room, Shift,
    StudentDetail, Lesson, Attendance, AttendanceStatus
)
from .forms import (
    LoginForm, UserForm, CourseForm, LessonForm,
    AttendanceForm, StudentEnrollmentForm
)
from .decorators import role_required
import logging

logger = logging.getLogger(__name__)


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user and user.is_active:
                login(request, user)
                logger.info(f"User {username} logged in successfully")
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials or inactive account')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout"""
    username = request.user.username
    logout(request)
    logger.info(f"User {username} logged out")
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard view - role-based content"""
    user = request.user
    context = {'user': user}

    if user.is_superadmin():
        # Superadmin dashboard
        context.update({
            'total_admins': User.objects.filter(role__name='admin').count(),
            'total_teachers': User.objects.filter(role__name='teacher').count(),
            'total_students': User.objects.filter(role__name='student').count(),
            'total_courses': Course.objects.filter(is_active=True).count(),
            'recent_activities': [],  # Can be implemented later
        })
        return render(request, 'dashboard/superadmin.html', context)

    elif user.is_admin():
        # Admin dashboard
        context.update({
            'total_teachers': User.objects.filter(role__name='teacher').count(),
            'total_students': User.objects.filter(role__name='student').count(),
            'total_courses': Course.objects.filter(is_active=True).count(),
            'active_courses': Course.objects.filter(is_active=True)[:5],
        })
        return render(request, 'dashboard/admin.html', context)

    elif user.is_teacher():
        # Teacher dashboard
        assigned_courses = Course.objects.filter(teacher=user, is_active=True)
        context.update({
            'assigned_courses': assigned_courses,
            'total_students': StudentDetail.objects.filter(course__in=assigned_courses).count(),
            'recent_lessons': Lesson.objects.filter(course__in=assigned_courses)[:5],
        })
        return render(request, 'dashboard/teacher.html', context)

    elif user.is_student():
        # Student dashboard
        enrolled_courses = StudentDetail.objects.filter(user=user)
        context.update({
            'enrolled_courses': enrolled_courses,
            'attendance_avg': enrolled_courses.aggregate(
                avg=Avg('attendance_percentage')
            )['avg'] or 0,
        })
        return render(request, 'dashboard/student.html', context)

    return render(request, 'dashboard/default.html', context)


# User Management Views
@login_required
@role_required(['superadmin'])
def admin_list(request):
    """List all admins (Superadmin only)"""
    admins = User.objects.filter(role__name='admin').order_by('first_name')
    return render(request, 'users/admin_list.html', {'admins': admins})


@login_required
@role_required(['superadmin'])
def admin_create(request):
    """Create new admin (Superadmin only)"""
    if request.method == 'POST':
        form = UserForm(request.POST, role_name='admin')
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    logger.info(f"Admin {user.username} created by {request.user.username}")
                    messages.success(request, f'Admin {user.full_name} created successfully')
                    return redirect('admin_list')
            except Exception as e:
                messages.error(request, f'Error creating admin: {str(e)}')
    else:
        form = UserForm(role_name='admin')

    return render(request, 'users/admin_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(['admin'])
def teacher_list(request):
    """List all teachers (Admin only)"""
    teachers = User.objects.filter(role__name='teacher').order_by('first_name')
    return render(request, 'users/teacher_list.html', {'teachers': teachers})


@login_required
@role_required(['admin'])
def teacher_create(request):
    """Create new teacher (Admin only)"""
    if request.method == 'POST':
        form = UserForm(request.POST, role_name='teacher')
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    logger.info(f"Teacher {user.username} created by {request.user.username}")
                    messages.success(request, f'Teacher {user.full_name} created successfully')
                    return redirect('teacher_list')
            except Exception as e:
                messages.error(request, f'Error creating teacher: {str(e)}')
    else:
        form = UserForm(role_name='teacher')

    return render(request, 'users/teacher_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(['admin'])
def student_list(request):
    """List all students (Admin only)"""
    students = User.objects.filter(role__name='student').order_by('first_name')
    return render(request, 'users/student_list.html', {'students': students})


@login_required
@role_required(['admin'])
def student_create(request):
    """Create new student (Admin only)"""
    if request.method == 'POST':
        form = UserForm(request.POST, role_name='student')
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    logger.info(f"Student {user.username} created by {request.user.username}")
                    messages.success(request, f'Student {user.full_name} created successfully')
                    return redirect('student_list')
            except Exception as e:
                messages.error(request, f'Error creating student: {str(e)}')
    else:
        form = UserForm(role_name='student')

    return render(request, 'users/student_form.html', {'form': form, 'action': 'Create'})


# Course Management Views
@login_required
@role_required(['admin', 'superadmin'])
def course_list(request):
    """List all courses"""
    courses = Course.objects.filter(is_active=True).select_related(
        'level', 'room', 'shift', 'teacher'
    ).order_by('name')
    return render(request, 'courses/course_list.html', {'courses': courses})


@login_required
@role_required(['admin'])
def course_create(request):
    """Create new course (Admin only)"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save()
                    logger.info(f"Course '{course.name}' created by {request.user.username}")
                    messages.success(request, f'Course {course.name} created successfully')
                    return redirect('course_list')
            except Exception as e:
                messages.error(request, f'Error creating course: {str(e)}')
    else:
        form = CourseForm()

    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(['admin'])
def course_edit(request, course_id):
    """Edit course (Admin only)"""
    course = get_object_or_404(Course, id=course_id, is_active=True)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save()
                    logger.info(f"Course '{course.name}' updated by {request.user.username}")
                    messages.success(request, f'Course {course.name} updated successfully')
                    return redirect('course_list')
            except Exception as e:
                messages.error(request, f'Error updating course: {str(e)}')
    else:
        form = CourseForm(instance=course)

    return render(request, 'courses/course_form.html', {
        'form': form,
        'course': course,
        'action': 'Edit'
    })


@login_required
@role_required(['teacher'])
def teacher_courses(request):
    """List courses assigned to teacher"""
    courses = Course.objects.filter(
        teacher=request.user,
        is_active=True
    ).select_related('level', 'room', 'shift')

    return render(request, 'courses/teacher_courses.html', {'courses': courses})


@login_required
@role_required(['teacher'])
def course_students(request, course_id):
    """View students in a course (Teacher only - for their courses)"""
    course = get_object_or_404(Course, id=course_id, teacher=request.user, is_active=True)
    students = StudentDetail.objects.filter(course=course).select_related('user')

    return render(request, 'courses/course_students.html', {
        'course': course,
        'students': students
    })


# Attendance Management Views
@login_required
@role_required(['teacher'])
def lesson_create(request, course_id):
    """Create lesson and mark attendance"""
    course = get_object_or_404(Course, id=course_id, teacher=request.user, is_active=True)

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    lesson = form.save(commit=False)
                    lesson.course = course
                    lesson.save()

                    # No longer redirecting immediately to mark_attendance
                    logger.info(f"Lesson '{lesson.topic}' created for course '{course.name}'")
                    messages.success(request, f'Lesson "{lesson.topic}" created successfully')
                    return redirect('teacher_courses') # Redirect to somewhere sensible.
            except Exception as e:
                messages.error(request, f'Error creating lesson: {str(e)}')
    else:
        form = LessonForm()

    return render(request, 'lessons/lesson_form.html', {
        'form': form,
        'course': course,
        'action': 'Create'
    })


@login_required
@role_required(['teacher'])
def mark_attendance(request, lesson_id):
    """Mark attendance for a lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
    students = StudentDetail.objects.filter(course=lesson.course).select_related('user')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                for student_detail in students:
                    status_id = request.POST.get(f'student_{student_detail.user.id}')
                    if status_id:
                        status = get_object_or_404(AttendanceStatus, id=status_id)

                        attendance, created = Attendance.objects.get_or_create(
                            lesson=lesson,
                            student=student_detail.user,
                            defaults={
                                'status': status,
                                'marked_by': request.user  # Assign the current user as marker
                            }
                        )

                        if not created:
                            attendance.status = status
                            attendance.marked_by = request.user # Ensure it's updated too!
                            attendance.save()

                messages.success(request, 'Attendance marked successfully')
                logger.info(f"Attendance marked for lesson '{lesson.topic}' by {request.user.username}")
                return redirect('teacher_courses')

        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')

    # Get existing attendance records
    existing_attendance = {
        att.student.id: att.status.id
        for att in lesson.attendances.all()
    }

    statuses = AttendanceStatus.objects.all()

    return render(request, 'lessons/mark_attendance.html', {
        'lesson': lesson,
        'students': students,
        'statuses': statuses,
        'existing_attendance': existing_attendance
    })


@login_required
def student_attendance(request):
    """View student's own attendance"""
    if not request.user.is_student():
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    enrolled_courses = StudentDetail.objects.filter(user=request.user).select_related('course')
    attendance_data = []

    for enrollment in enrolled_courses:
        course_attendance = Attendance.objects.filter(
            student=request.user,
            lesson__course=enrollment.course
        ).select_related('lesson', 'status')

        attendance_data.append({
            'course': enrollment.course,
            'attendance_percentage': enrollment.attendance_percentage,
            'attendance_records': course_attendance
        })

    return render(request, 'attendance/student_attendance.html', {
        'attendance_data': attendance_data
    })


# Student Enrollment (Admin only)
@login_required
@role_required(['admin'])
def enroll_student(request):
    """Enroll student in courses"""
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.cleaned_data['student']
                    courses = form.cleaned_data['courses']

                    for course in courses:
                        StudentDetail.objects.get_or_create(
                            user=student,
                            course=course
                        )

                    messages.success(request, f'Student {student.full_name} enrolled successfully')
                    logger.info(f"Student {student.username} enrolled in courses by {request.user.username}")
                    return redirect('student_list')
            except Exception as e:
                messages.error(request, f'Error enrolling student: {str(e)}')
    else:
        form = StudentEnrollmentForm()

    return render(request, 'enrollment/enroll_student.html', {'form': form})