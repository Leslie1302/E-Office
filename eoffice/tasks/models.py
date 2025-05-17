from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    STATUS_CHOICES = [
        ('dispatched-officer', 'Dispatched to officer'),
        ('draft', 'Draft'),
        ('finalized-draft', 'Finalized draft'),
        ('signed-dispatched', 'Signed and dispatched to CD/HM'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='dispatched-officer')
    deadline = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to='task_files/', null=True, blank=True)

    def __str__(self):
        return self.title

    def get_progress(self):
        progress_map = {
            'dispatched-officer': 25,
            'draft': 50,
            'finalized-draft': 75,
            'signed-dispatched': 100,
        }
        return progress_map.get(self.status, 0)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    tasks = models.ManyToManyField(Task, related_name='reminders')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_reminders')
    is_active = models.BooleanField(default=True)
    message = models.TextField(blank=True, null=True)
    is_dismissed = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder for {self.user.username} by {self.created_by.username}"