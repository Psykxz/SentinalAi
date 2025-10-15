from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_user = models.BooleanField(default=True)

    def __str__(self):
        return self.username
    
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=30, unique=True)  # can be username or email
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female")])
    password = models.CharField(max_length=128)  # hashed password
    role = models.CharField(max_length=8, choices=[("admin", "Admin"), ("user", "User")], default="user")
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class TextContent(models.Model):
    text_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=100)   # text input from user
    submission_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Text {self.text_id} by {self.user.username}"

class ImageContent(models.Model):
    image_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filePath = models.CharField(max_length=100)  # path to uploaded file
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.image_id} by {self.user.username}"

class OCRResult(models.Model):
    ocr_id = models.AutoField(primary_key=True)
    image = models.ForeignKey(ImageContent, on_delete=models.CASCADE)
    extractedText = models.CharField(max_length=100)
    extractionTime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OCR {self.ocr_id} for Image {self.image.image_id}"

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ContentAnalysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    sourceType = models.CharField(max_length=30)  # "text" or "image"
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    source_object = GenericForeignKey('content_type', 'object_id')
    isFlagged = models.BooleanField(default=False)
    severityLevel = models.CharField(max_length=10, choices=[("Low", "Low"), ("Medium", "Medium"), ("High", "High")], null=True, blank=True)
    detectedLabels = models.CharField(max_length=225, null=True, blank=True)
    analysisTime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis {self.analysis_id} [{self.sourceType}]"

class EmojiAnalysis(models.Model):
    emoji_id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=30)      # emoji character
    meaning = models.CharField(max_length=255)    # emoji interpretation

    def __str__(self):
        return f"{self.symbol} - {self.meaning}"

class SlangInterpretation(models.Model):
    slang_id = models.AutoField(primary_key=True)
    slangText = models.CharField(max_length=30)
    meaning = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.slangText} -> {self.meaning}"
    
class ActivityLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activityType = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    timeStamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timeStamp']

    def __str__(self):
        return f"Activity {self.log_id} by {self.user.username}"
    
class Feedback(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    feedback_id = models.AutoField(primary_key=True)
    analysis = models.ForeignKey(ContentAnalysis, on_delete=models.CASCADE)
    correctLabel = models.CharField(max_length=50, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    submittedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    submittedAt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Feedback {self.feedback_id} for Analysis {self.analysis.analysis_id}"
