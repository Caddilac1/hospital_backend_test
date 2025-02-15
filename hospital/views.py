from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from cryptography.fernet import Fernet
from .tasks import schedule_reminders
from .tasks import send_checkin_reminder
from .models import CheckIn
from .serializers import CheckInSerializer
from .gemini_utils import extract_actionable_steps
from .models import User, Doctor, Patient, Note
from .serializers import UserSerializer, DoctorSerializer, PatientSerializer, NoteSerializer
import os

# Load encryption key from environment variables (must be set in production)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("Encryption key not found! Set ENCRYPTION_KEY in environment variables.")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())  # Ensure encoding


def get_tokens_for_user(user):
    """Generates JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserViewSet(viewsets.ModelViewSet):
    """Handles user registration, login, and profile management."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Allow all users to register/login without authentication

    def get_queryset(self):
        """Ensure users can only see their own profile."""
        if self.request.user.is_authenticated:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registers a new user (No authentication required)."""
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        user_type = request.data.get('user_type')

        if not username or not email or not password or not user_type:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password, user_type=user_type)

        if user_type == 'patient':
            Patient.objects.create(user=user)
        elif user_type == 'doctor':
            Doctor.objects.create(user=user)

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Logs in a user and returns JWT tokens."""
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)

        if user:
            tokens = get_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Handles user logout (JWT tokens should be managed client-side)."""
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class PatientViewSet(viewsets.ModelViewSet):
    """Handles patient data and doctor assignments."""

    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Restrict patients to only see their own profile."""
        if self.request.user.user_type == 'patient':
            return Patient.objects.filter(user=self.request.user)
        return Patient.objects.all()

    @action(detail=False, methods=['post'])
    def assign_doctor(self, request):
        """Assigns a doctor to a patient."""
        patient = get_object_or_404(Patient, user=request.user)
        doctor_id = request.data.get('doctor_id')
        doctor = get_object_or_404(Doctor, id=doctor_id)
        patient.doctor = doctor
        patient.save()
        return Response({'message': 'Doctor assigned successfully'}, status=status.HTTP_200_OK)


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Allows users to view doctors (read-only)."""

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]


class NoteViewSet(viewsets.ModelViewSet):
    """Handles encrypted doctor notes and actionable steps."""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Restrict notes visibility based on user role."""
        user = self.request.user
        if user.user_type == 'doctor':
            return Note.objects.filter(doctor=user.doctor)
        elif user.user_type == 'patient':
            return Note.objects.filter(patient=user.patient)
        return Note.objects.none()

    def perform_create(self, serializer):
        """Doctors submit encrypted notes, and AI extracts actionable steps."""
        user = self.request.user
        if user.user_type != 'doctor':
            raise PermissionError("Only doctors can create notes.")

        text = self.request.data.get('text')
        if not text:
            raise ValueError("Note text is required.")

        encrypted_text = cipher_suite.encrypt(text.encode()).decode()
        actionable_steps = extract_actionable_steps(text)

        note = serializer.save(doctor=user.doctor, encrypted_text=encrypted_text, actionable_steps=actionable_steps)

        # Cancel old reminders and schedule new ones
        schedule_reminders.delay(note.id)

    @action(detail=True, methods=['get'])
    def decrypt(self, request, pk=None):
        """Allows authorized users to decrypt and view notes."""
        note = self.get_object()
        decrypted_text = cipher_suite.decrypt(note.encrypted_text.encode()).decode()
        return Response({'decrypted_text': decrypted_text}, status=status.HTTP_200_OK)



class CheckInViewSet(viewsets.ModelViewSet):
    """Handles patient check-ins."""
    
    serializer_class = CheckInSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Ensure patients see only their own check-ins."""
        return CheckIn.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        """Automatically associate patient and create a check-in."""
        serializer.save(patient=self.request.user)
        send_checkin_reminder.delay(self.request.user.id)  # Celery task for reminders

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Marks a check-in as completed."""
        checkin = self.get_object()
        checkin.completed = True
        checkin.save()
        return Response({'message': 'Check-in marked as completed'}, status=status.HTTP_200_OK)