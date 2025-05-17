from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        is_manager = instance.is_superuser  # Superusers are managers by default
        Profile.objects.create(user=instance, is_manager=is_manager, phone_number='+1234567890')