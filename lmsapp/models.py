# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Role(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Superadmin'),
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class User(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role.name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_superadmin(self):
        return self.role.name == 'superadmin'

    def is_admin(self):
        return self.role.name == 'admin'

    def is_teacher(self):
        return self.role.name == 'teacher'

    def is_student(self):
        return self.role.name == 'student'


class Level(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('elementary', 'Elementary'),
        ('intermediate', 'Intermediate'),
        ('upper_intermediate', 'Upper Intermediate'),
        ('advanced', 'Advanced'),
    ]

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)

    def __str__(self):
        return self.get_level_display()


class Room(models.Model):
    number = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField(default=20)

    def __str__(self):
        return f"Room {self.number}"


class Shift(models.Model):
    name = models.CharField(max_length=50)  # e.g., "Morning 9:00-11:00"
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    level = models.ForeignKey(Level, on_delete=models.PROTECT)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    teacher = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={'role__name': 'teacher'},
        related_name='teaching_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['room', 'shift']  # One course per room per shift

    def __str__(self):
        return f"{self.name} - {self.level} ({self.shift})"


class StudentDetail(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role__name': 'student'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    attendance_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    class Meta:
        unique_together = ['user', 'course']  # Student can enroll in course only once

    def __str__(self):
        return f"{self.user.full_name} - {self.course.name}"

    def update_attendance_percentage(self):
        """Calculate and update attendance percentage"""
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            self.attendance_percentage = 0.0
        else:
            present_count = self.attendances.filter(status__name='present').count()
            self.attendance_percentage = (present_count / total_lessons) * 100
        self.save()


class Lesson(models.Model):
    topic = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['course', 'date']  # One lesson per course per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.course.name} - {self.topic} ({self.date})"


class AttendanceStatus(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    name = models.CharField(max_length=10, choices=STATUS_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class Attendance(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role__name': 'student'},
        related_name='attendances'
    )
    status = models.ForeignKey(AttendanceStatus, on_delete=models.PROTECT)
    marked_at = models.DateTimeField(auto_now_add=True)
    marked_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={'role__name': 'teacher'},
        related_name='marked_attendances'
    )

    class Meta:
        unique_together = ['lesson', 'student']  # One attendance record per student per lesson

    def __str__(self):
        return f"{self.student.full_name} - {self.lesson} - {self.status}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update student's attendance percentage after marking attendance
        try:
            student_detail = StudentDetail.objects.get(
                user=self.student,
                course=self.lesson.course
            )
            student_detail.update_attendance_percentage()
        except StudentDetail.DoesNotExist:
            pass