from django import forms
from .models import Task
from django.contrib.auth.models import User

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assignee', 'deadline', 'status', 'file']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'file': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            self.fields['assignee'].queryset = User.objects.filter(id=user.id)
            self.fields['status'].choices = [
                ('Draft', 'Draft'),
                ('Finalized draft', 'Finalized draft'),
                ('Signed and dispatched to CD/HM', 'Signed and dispatched to CD/HM'),
            ]  # Employees can't set 'Dispatched to officer'