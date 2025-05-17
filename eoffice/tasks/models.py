from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Task(models.Model):
    STATUS_CHOICES = [
        ('Dispatched to officer', 'Dispatched to officer'),
        ('Draft', 'Draft'),
        ('Finalized draft', 'Finalized draft'),
        ('Signed and dispatched to CD/HM', 'Signed and dispatched to CD/HM'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Dispatched to officer')
    file = models.FileField(upload_to='task_files/', blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Set progress based on status
        status_progress = {
            'Dispatched to officer': 25,
            'Draft': 50,
            'Finalized draft': 75,
            'Signed and dispatched to CD/HM': 100,
        }
        self.is_archived = self.status == 'Signed and dispatched to CD/HM'
        super().save(*args, **kwargs)

    def get_progress(self):
        status_progress = {
            'Dispatched to officer': 25,
            'Draft': 50,
            'Finalized draft': 75,
            'Signed and dispatched to CD/HM': 100,
        }
        return status_progress.get(self.status, 0)

    def __str__(self):
        return self.title