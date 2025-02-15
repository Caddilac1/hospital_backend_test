from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'user_type']

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        extra_kwargs['password'] = {'write_only': False}  # Make it visible in the form
        return extra_kwargs

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Patient
        fields = ['id', 'user', 'doctor']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Doctor
        fields = ['id', 'user']

class NoteSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer()
    patient = PatientSerializer()

    class Meta:
        model = Note
        fields = ['id', 'doctor', 'patient', 'encrypted_text', 'created_at']

class ActionableStepSerializer(serializers.ModelSerializer):
    note = NoteSerializer()

    class Meta:
        model = ActionableStep
        fields = ['id', 'note', 'step_type', 'description', 'scheduled_date', 'completed']


class CheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = ['id', 'patient', 'timestamp', 'completed']
        read_only_fields = ['patient', 'timestamp']

