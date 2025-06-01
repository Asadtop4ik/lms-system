# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Role, Course, Level, Room, Shift, Lesson, StudentDetail


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )


class UserForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.role_name = kwargs.pop('role_name', None)
        super().__init__(*args, **kwargs)

        # Make email required
        self.fields['email'].required = True

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if self.role_name:
            role = Role.objects.get(name=self.role_name)
            user.role = role

        if commit:
            user.save()
        return user


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'level', 'room', 'shift', 'teacher']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'shift': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter teachers only
        self.fields['teacher'].queryset = User.objects.filter(role__name='teacher', is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        shift = cleaned_data.get('shift')

        if room and shift:
            # Check if room-shift combination is already taken
            existing_course = Course.objects.filter(
                room=room,
                shift=shift,
                is_active=True
            )

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                existing_course = existing_course.exclude(pk=self.instance.pk)

            if existing_course.exists():
                raise ValidationError(
                    f"Room {room.number} is already booked for {shift.name}"
                )

        return cleaned_data


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['topic', 'date']
        widgets = {
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter lesson topic'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and hasattr(self, 'course'):
            # Check if lesson already exists for this course on this date
            if Lesson.objects.filter(course=self.course, date=date).exists():
                raise ValidationError(
                    f"A lesson already exists for this course on {date}"
                )
        return date


class AttendanceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        students = kwargs.pop('students', [])
        super().__init__(*args, **kwargs)

        from .models import AttendanceStatus
        status_choices = [(s.id, s.get_name_display()) for s in AttendanceStatus.objects.all()]

        for student in students:
            self.fields[f'student_{student.id}'] = forms.ChoiceField(
                choices=[('', '-- Select Status --')] + status_choices,
                required=True,
                widget=forms.Select(attrs={'class': 'form-control'})
            )


class StudentEnrollmentForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role__name='student', is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="-- Select Student --"
    )
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        courses = cleaned_data.get('courses')

        if student and courses:
            # Check for existing enrollments
            existing_enrollments = StudentDetail.objects.filter(
                user=student,
                course__in=courses
            ).values_list('course__name', flat=True)

            if existing_enrollments:
                course_names = ', '.join(existing_enrollments)
                raise ValidationError(
                    f"Student is already enrolled in: {course_names}"
                )

        return cleaned_data


class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...'
        })
    )


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date")

        return cleaned_data