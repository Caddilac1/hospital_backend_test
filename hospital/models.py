from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid


USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )

NOTE_TYPE_CHOICES = (
        ('checklist', 'Checklist'),
        ('plan', 'Plan'),
    )

class User(AbstractUser):
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient')
    doctor = models.ForeignKey('Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')

    def __str__(self):
        return self.user.email

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')

class Note(models.Model):
    doctor = models.ForeignKey("Doctor", on_delete=models.CASCADE)
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    encrypted_text = models.TextField()
    actionable_steps = models.JSONField(default=dict)  # Store checklist & plan

class ActionableStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='steps')
    step_type = models.CharField(max_length=10, choices=NOTE_TYPE_CHOICES)
    description = models.TextField()
    scheduled_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def mark_completed(self):
        self.completed = True
        self.save()


class CheckIn(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.username} - {'Completed' if self.completed else 'Pending'}"

