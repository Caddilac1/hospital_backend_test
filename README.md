Hospital Backend System

Overview
This is a backend system for a hospital that manages user authentication, patient-doctor assignments, doctor note submissions, and dynamic scheduling of actionable steps based on AI-driven processing. The system ensures data security, efficient task scheduling, and role-based access control.

Authentication & Security
User Authentication
JWT Authentication (via djangorestframework-simplejwt) is used to secure API endpoints.
Users receive access and refresh tokens upon login, ensuring secure authentication.
API endpoints requiring authentication are protected with IsAuthenticated.

Password Storage
Passwords are hashed using Django's built-in authentication system (make_password).
This ensures that passwords are not stored in plain text, reducing security risks.

Encryption of Doctor Notes
Doctor notes are encrypted using Fernet encryption (AES-128 CBC mode) before being stored in the database.

Why encryption?
Only authorized users (doctor & patient) can read the notes.
Prevents unauthorized access even if the database is compromised.
The encryption key is stored as an environment variable (ENCRYPTION_KEY) and never hardcoded.

Patient–Doctor Assignment
How it Works
Upon registration, users choose a role:
Doctor → Manages patients and writes notes.
Patient → Selects a doctor and receives notes.
Patients must select a doctor after signing up.
Doctors can view their assigned patients through an endpoint.

Doctor Notes & Actionable Steps
Doctor Notes Submission
Doctors submit encrypted notes for their patients.
AI (Gemini API) extracts actionable steps, dividing them into:
Checklist → One-time tasks (e.g., "Buy a drug").
Plan → Scheduled actions (e.g., "Take drug for 7 days").


Why AI-Driven Actionable Steps?
Automates medical recommendations without manual intervention.
Ensures structured and organized follow-up steps for patients.
Allows easy scheduling of reminders for patients.


Dynamic Scheduling & Reminders
How Reminders Work
When a doctor submits a note, the previously scheduled tasks are canceled to avoid redundancy.
New reminders are scheduled dynamically based on the AI-generated plan.
The system ensures missed reminders are rescheduled until completion.
Check-in System for Task Completion
Patients check-in via an API endpoint to confirm task completion.
If a patient misses a check-in, the system automatically extends the reminder period.


Why Celery for Scheduling?
Asynchronous task execution prevents blocking API responses.
Ensures scalability by running tasks in the background.
Supports periodic reminders without overloading the system.


Technology              Stack
Component	        Technology Used
Backend Framework	Django REST Framework (DRF)
Authentication	    JWT (djangorestframework-simplejwt)
Database	        SQLite (for dev)
AI Model	        Google Gemini API
Encryption	        Cryptography (Fernet AES)
Task Scheduling	    Celery + Redis

This backend system ensures secure, efficient, and AI-powered medical task management. It provides role-based authentication, secure data handling, and smart scheduling for patient care.


