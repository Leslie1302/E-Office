from django import forms
from .models import Task, Profile
from django.contrib.auth.models import User

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'deadline', 'assignee', 'file']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'file': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            self.fields['status'].choices = [
                ('dispatched-officer', 'Dispatched to officer'),
                ('draft', 'Draft'),
                ('finalized-draft', 'Finalized draft'),
                ('signed-dispatched', 'Signed and dispatched to CD/HM'),
            ]
            self.fields['assignee'].queryset = User.objects.filter(id=user.id)  # Employees can't change assignee
        else:
            self.fields['assignee'].queryset = User.objects.all()

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data