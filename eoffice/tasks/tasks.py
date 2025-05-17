from celery import shared_task
import requests

@shared_task
def send_task_assignment_notification(task_id, assignee_id):
    from .models import Task, Profile
    from django.contrib.auth.models import User

    try:
        task = Task.objects.get(id=task_id)
        assignee = User.objects.get(id=assignee_id)
        profile = Profile.objects.get(user=assignee)

        # SMS notification via TextBelt
        if profile.phone_number:
            sms_body = (
                f"New task assigned: {task.title}. "
                f"Deadline: {task.deadline}. "
                f"View: http://127.0.0.1:8000/tasks/employee/dashboard/"
            )
            response = requests.post('https://textbelt.com/text', {
                'phone': profile.phone_number,  # e.g., +233241234567
                'message': sms_body,
                'key': 'textbelt',  # Free key for 1 SMS/day
            })
            if response.json()['success']:
                print(f"SMS sent to {profile.phone_number}")
            else:
                print(f"SMS failed: {response.json()['error']}")
        else:
            print(f"No phone number for user {assignee.username}")

    except User.DoesNotExist:
        print(f"User with id {assignee_id} does not exist.")
    except Profile.DoesNotExist:
        print(f"Profile for user {assignee.username} does not exist.")
    except Exception as e:
        print(f"Error sending notification for task {task_id}: {str(e)}")