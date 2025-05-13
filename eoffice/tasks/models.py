from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    TASK_TYPES = (
        ('letter', 'Letter'),
        ('memo', 'Memo'),
        ('report', 'Report'),
        ('invoice', 'Invoice'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
        ('archived', 'Archived'),
        ('returned', 'Returned'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=10, choices=TASK_TYPES)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
