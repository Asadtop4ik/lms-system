# decorators.py
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    Usage: @role_required(['admin', 'superadmin'])
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            user_role = request.user.role.name
            if user_role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def superadmin_required(view_func):
    """Decorator for superadmin-only views"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superadmin():
            messages.error(request, 'Superadmin access required.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Decorator for admin-only views"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_admin():
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


def teacher_required(view_func):
    """Decorator for teacher-only views"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_teacher():
            messages.error(request, 'Teacher access required.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


def student_required(view_func):
    """Decorator for student-only views"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_student():
            messages.error(request, 'Student access required.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper