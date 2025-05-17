from celery import shared_task
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
from tasks.models import Task
from datetime import datetime, timedelta
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import Profile

@shared_task
def send_task_assignment_notification(task_id):
    try:
        task = Task.objects.get(id=task_id)
        assignee = task.assignee
        if assignee.email:
            send_mail(
                subject=f'New Task Assigned: {task.title}',
                message=f'You have been assigned a new task:\n\nTitle: {task.title}\nDescription: {task.description}\nDeadline: {task.deadline}\n\nPlease check the E-Office Task Manager for details.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[assignee.email],
                fail_silently=False,
            )
        if hasattr(assignee, 'profile') and assignee.profile.phone_number:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f'New Task: {task.title}. Deadline: {task.deadline}. Check E-Office Task Manager.',
                from_=settings.TWILIO_PHONE_NUMBER,
                to=assignee.profile.phone_number
            )
    except Exception as e:
        print(f"Error sending notification: {e}")

@shared_task
def check_deadline_reminders():
    three_days_from_now = timezone.now().date() + timedelta(days=3)
    tasks = Task.objects.filter(
        deadline__lte=three_days_from_now,
        deadline__gte=timezone.now().date(),
        status__in=['Pending', 'In Progress']
    )
    for task in tasks:
        assignee = task.assignee
        if assignee.email:
            send_mail(
                subject=f'Reminder: Task "{task.title}" Due Soon',
                message=f'The task "{task.title}" is due on {task.deadline}. Please complete it soon.\nDescription: {task.description}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[assignee.email],
                fail_silently=False,
            )
        if hasattr(assignee, 'profile') and assignee.profile.phone_number:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f'Reminder: Task "{task.title}" due on {task.deadline}. Check E-Office Task Manager.',
                from_=settings.TWILIO_PHONE_NUMBER,
                to=assignee.profile.phone_number
            )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        is_manager = instance.is_superuser  # Superusers are managers by default
        Profile.objects.create(user=instance, is_manager=is_manager, phone_number='+1234567890')