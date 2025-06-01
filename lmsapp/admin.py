# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Role, Course, Level, Room, Shift,
    StudentDetail, Lesson, Attendance, AttendanceStatus
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_display_name']
    list_filter = ['name']
    search_fields = ['name']

    def get_display_name(self, obj):
        return obj.get_name_display()

    get_display_name.short_description = 'Display Name'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['username']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('first_name', 'last_name', 'role')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('role')


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'get_display_name']
    list_filter = ['level']

    def get_display_name(self, obj):
        return obj.get_level_display()

    get_display_name.short_description = 'Display Name'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'capacity']
    search_fields = ['number']
    ordering = ['number']


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'duration']
    list_filter = ['start_time', 'end_time']
    ordering = ['start_time']

    def duration(self, obj):
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), obj.start_time)
        end = datetime.combine(datetime.today(), obj.end_time)
        duration = end - start
        return str(duration)

    duration.short_description = 'Duration'


class StudentDetailInline(admin.TabularInline):
    model = StudentDetail
    extra = 0
    readonly_fields = ['attendance_percentage', 'enrollment_date']
    fields = ['user', 'attendance_percentage', 'enrollment_date']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'level', 'teacher', 'room', 'shift',
        'student_count', 'is_active', 'created_at'
    ]
    list_filter = ['level', 'is_active', 'created_at', 'shift']
    search_fields = ['name', 'teacher__first_name', 'teacher__last_name']
    ordering = ['name']
    inlines = [StudentDetailInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'level', 'teacher', 'room', 'shift'
        ).prefetch_related('studentdetail_set')

    def student_count(self, obj):
        count = obj.studentdetail_set.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'red',
            count
        )

    student_count.short_description = 'Students'


@admin.register(StudentDetail)
class StudentDetailAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'course', 'attendance_percentage',
        'enrollment_date', 'attendance_status'
    ]
    list_filter = ['course', 'enrollment_date']
    search_fields = ['user__first_name', 'user__last_name', 'course__name']
    readonly_fields = ['attendance_percentage', 'enrollment_date']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'course')

    def attendance_status(self, obj):
        percentage = obj.attendance_percentage
        if percentage >= 80:
            color = 'green'
            status = 'Good'
        elif percentage >= 60:
            color = 'orange'
            status = 'Average'
        else:
            color = 'red'
            status = 'Poor'

        return format_html(
            '<span style="color: {};">{} ({}%)</span>',
            color, status, round(percentage, 1)
        )

    attendance_status.short_description = 'Attendance Status'


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    readonly_fields = ['marked_at', 'marked_by']
    fields = ['student', 'status', 'marked_by', 'marked_at']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['topic', 'course', 'date', 'attendance_count', 'created_at']
    list_filter = ['course', 'date', 'created_at']
    search_fields = ['topic', 'course__name']
    ordering = ['-date']
    inlines = [AttendanceInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course').prefetch_related('attendances')

    def attendance_count(self, obj):
        count = obj.attendances.count()
        total_students = obj.course.studentdetail_set.count()

        if total_students == 0:
            return format_html('<span style="color: gray;">No students</span>')

        percentage = (count / total_students) * 100 if total_students > 0 else 0
        color = 'green' if percentage == 100 else 'orange' if percentage >= 50 else 'red'

        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color, count, total_students, round(percentage, 1)
        )

    attendance_count.short_description = 'Attendance'


@admin.register(AttendanceStatus)
class AttendanceStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_display_name', 'usage_count']

    def get_display_name(self, obj):
        return obj.get_name_display()

    get_display_name.short_description = 'Display Name'

    def usage_count(self, obj):
        count = obj.attendance_set.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    usage_count.short_description = 'Times Used'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'lesson', 'status', 'marked_by', 'marked_at'
    ]
    list_filter = ['status', 'marked_at', 'lesson__course']
    search_fields = [
        'student__first_name', 'student__last_name',
        'lesson__topic', 'lesson__course__name'
    ]
    ordering = ['-marked_at']
    date_hierarchy = 'marked_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'lesson', 'lesson__course', 'status', 'marked_by'
        )


# Customize admin site header
admin.site.site_header = "IKnow Academy LMS Administration"
admin.site.site_title = "LMS Admin"
admin.site.index_title = "Learning Management System"