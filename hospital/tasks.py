from celery import shared_task
from django.utils.timezone import now
from .models import Note
import time
from django.core.mail import send_mail
from .models import User


@shared_task
def send_reminder(note_id, task_name):
    """Send a reminder for a specific task in the plan."""
    note = Note.objects.get(id=note_id)
    patient = note.patient.user
    print(f"Reminder for {patient.email}: {task_name}")

@shared_task
def schedule_reminders(note_id):
    """Schedules all reminders for a doctor's note."""
    note = Note.objects.get(id=note_id)
    if not note.actionable_steps:
        return

    for step in note.actionable_steps.get("plan", []):
        task_name = step["task"]
        frequency = step["frequency"]
        duration = int(step["duration"].split()[0])  # Extract number of days

        for day in range(duration):
            time.sleep(2)  
            send_reminder.apply_async((note.id, task_name), countdown=day * 86400)  



@shared_task
def send_checkin_reminder(user_id):
    """Sends a reminder email for check-in completion."""
    user = User.objects.get(id=user_id)
    send_mail(
        "Check-In Reminder",
        "Please complete your check-in for today.",
        "admin@hospital.com",
        [user.email],
        fail_silently=False,
    )            
