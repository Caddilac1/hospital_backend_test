from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, DoctorViewSet, PatientViewSet, NoteViewSet, CheckInViewSet

# Using Django REST framework's router to automatically generate URL patterns
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'checkin', CheckInViewSet, basename='checkin')

urlpatterns = router.urls  # Auto-generates URLs for all viewsets

# Manually add custom actions that are not included in the default router
urlpatterns += [
    path('register/', UserViewSet.as_view({'post': 'register'}), name='register'),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='login'),
    path('logout/', UserViewSet.as_view({'post': 'logout'}), name='logout'),
    path('assign-doctor/', PatientViewSet.as_view({'post': 'assign_doctor'}), name='assign_doctor'),
]
