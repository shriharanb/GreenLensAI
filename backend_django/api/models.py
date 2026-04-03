from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

class Farmer(AbstractUser):
    phone = models.CharField(max_length=30)
    recovery_answer = models.CharField(max_length=255, blank=True, null=True)
    language_preference = models.CharField(max_length=10, default='en', help_text="e.g., 'en', 'ta', 'hi'")
    
    def __str__(self):
        return self.username


class OTPRecord(models.Model):
    OTP_TYPES = [
        ('mobile', 'Mobile'),
        ('email', 'Email'),
    ]
    user = models.ForeignKey(Farmer, on_delete=models.CASCADE, null=True, blank=True)
    pending_user = models.ForeignKey('PendingFarmer', on_delete=models.CASCADE, null=True, blank=True)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

class PendingFarmer(models.Model):
    username = models.CharField(max_length=150, unique=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    recovery_answer = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

class Conversation(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farmer.username} - {self.title}"

class ChatHistory(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='chats')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField(null=True, blank=True)
    image_path = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

class TreatmentPlan(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='treatment_plans')
    disease_name = models.CharField(max_length=255)
    start_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    current_day = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.farmer.username} - {self.disease_name} - Day {self.current_day}"

class TreatmentDay(models.Model):
    plan = models.ForeignKey(TreatmentPlan, on_delete=models.CASCADE, related_name='days')
    day_number = models.IntegerField()
    treatment_text = models.TextField()  # The extracted step for this day from RAG
    sent_to_farmer = models.BooleanField(default=False)
    farmer_photo_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ('plan', 'day_number')

    def __str__(self):
        return f"Plan {self.plan.id} - Day {self.day_number}"
