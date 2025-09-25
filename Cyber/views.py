from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import User, TextContent, ContentAnalysis, ImageContent, OCRResult, ActivityLog, Feedback
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# --- New Imports for ML and Preprocessing ---
import joblib
import os
import pandas as pd
from ml import utils
import pytesseract
from PIL import Image
from Cyber.slang_processor import load_slang_from_db, replace_slang, replace_emojis

# Set the path to the Tesseract executable (adjust as needed)
pytesseract.pytesseract.tesseract_cmd = r'D:\OCR\tesseract.exe'

# --- Load ML Model and Slang Dictionary globally for efficiency ---
# Define the path to your model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "D:\ROHIT MCA MINI PROJECT\myProject\ml\cyberbullying_model.pkl")

# Load the model and slang dictionary once when the server starts
try:
    pipeline = joblib.load(MODEL_PATH)
    slang_dict = load_slang_from_db()
    print("✅ Machine learning model and slang dictionary loaded successfully.")
except FileNotFoundError:
    pipeline = None
    slang_dict = None
    print(f"❌ Error: Model file not found at {MODEL_PATH}")
except Exception as e:
    pipeline = None
    slang_dict = None
    print(f"❌ An error occurred while loading: {e}")

# --- Existing Views (No changes needed) ---
def homepage(request):
    role = request.session.get("role", "guest")
    username = request.session.get("username", "Guest")
    return render(request, "homepage.html", {"role": role, "username": username})

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
            return redirect("login")
        if check_password(password, user.password):
            request.session['user_id'] = user.user_id
            request.session['username'] = user.username
            request.session['role'] = user.role.lower()
            if user.role.lower() == "admin":
                return redirect("admin_dashboard")
            else:
                return redirect("user_home")
        else:
            messages.error(request, "Invalid password.")
            return redirect("login")
    return render(request, "loginpage.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def admin_dashboard(request):
    if request.session.get("role") != "admin":
        return redirect("login")
    return render(request, "admin_dashboard.html")

def user_home(request):
    if request.session.get("role") != "user":
        return redirect("login")
    return render(request, "user_home.html",{"role": "user", "username": request.session.get("username", "User")})

def user_dashboard(request):
    if request.session.get("role") != "user":
        return redirect("login")
    return render(request, "user_home.html", {"username": request.session.get("username", "User")})

def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        full_name = request.POST['full_name']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        gender = request.POST['gender']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("register")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("register")
        User.objects.create(
            username=username,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            gender=gender,
            password=make_password(password1),
            status=True
        )
        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")
    return render(request, "register.html")

# --- Updated Analysis Views with Preprocessing Logic ---
def analyze_text(request):
    if request.method == "POST":
        user_text = request.POST.get("text_input")
        if not user_text:
            return render(request, 'user_home.html', {'error': 'Text input cannot be empty.'})

        if not request.session.get('user_id'):
            return redirect('login_view')

        try:
            current_user = User.objects.get(user_id=request.session['user_id'])
        except User.DoesNotExist:
            return redirect('login_view')

        # Log the text submission activity
        log_activity(current_user, 'Text Submission', f'Submitted text for analysis: "{user_text[:50]}..."')

        # --- Preprocessing Step (Emoji and Slang Interpretation) ---
        processed_text = replace_emojis(user_text)
        if slang_dict:
            processed_text = replace_slang(processed_text, slang_dict)

        # 2. Store the original text in TextContent table
        text_entry = TextContent.objects.create(
            user=current_user,
            content=user_text,
            submission_time=datetime.now()
        )

        # 3. Analyze the processed text using the ML model
        analysis_result = utils.predict_text(processed_text)
        detected_labels = analysis_result['label']
        severity = "High" if "bullying" in detected_labels.lower() or "threat" in detected_labels.lower() else "Low"

        # 4. Store the analysis result in ContentAnalysis table
        content_analysis_entry = ContentAnalysis.objects.create(
            sourceType='text',
            source_id=text_entry.text_id,
            isFlagged=True,
            severityLevel=severity,
            detectedLabels=detected_labels,
            analysisTime=datetime.now()
        )

        # Log the analysis result
        log_activity(current_user, 'Text Analysis', f'Analysis complete. Detected labels: {detected_labels}')

        recent_activities = ActivityLog.objects.filter(user=current_user).order_by('-timeStamp')[:10]

        return render(request, 'user_home.html', {
            'analysis_result': analysis_result,
            'user_text': user_text,
            'label': detected_labels,
            'analysis_id': content_analysis_entry.analysis_id, # Pass the analysis ID
            'recent_activities': recent_activities,
        })
    return redirect('user_home')

def analyze_image(request):
    if request.method == 'POST' and request.FILES.get('image_file'):
        uploaded_file = request.FILES['image_file']

        if not request.session.get('user_id'):
            return redirect('login_view')

        try:
            current_user = User.objects.get(user_id=request.session['user_id'])
        except User.DoesNotExist:
            return redirect('login_view')

        # Log the image upload activity
        log_activity(current_user, 'Image Upload', f'Uploaded image for analysis: "{uploaded_file.name}"')

        image_path = os.path.join("media", uploaded_file.name)
        with open(image_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        image_entry = ImageContent.objects.create(
            user=current_user,
            filePath=image_path,
            upload_time=datetime.now()
        )

        try:
            extracted_text = pytesseract.image_to_string(Image.open(uploaded_file))
        except Exception as e:
            return render(request, 'user_home.html', {'error': f'OCR failed: {e}'})
        
        if not extracted_text.strip():
            log_activity(current_user, 'Image OCR', 'No text detected in the uploaded image.')
            return render(request, 'user_home.html', {'ocr_result': 'No text detected in the image.'})

        # --- Preprocessing Step (Emoji and Slang Interpretation) ---
        processed_text = replace_emojis(extracted_text)
        if slang_dict:
            processed_text = replace_slang(processed_text, slang_dict)

        # 4. Store the OCR result in the OCRResult table
        ocr_entry = OCRResult.objects.create(
            image=image_entry,
            extractedText=extracted_text,
            extractionTime=datetime.now()
        )
        
        # 5. Analyze the processed text using the ML model
        analysis_result = utils.predict_text(processed_text)
        detected_labels = analysis_result['label']
        severity = "High" if "bullying" in detected_labels.lower() or "threat" in detected_labels.lower() else "Low"
        
        # 6. Store the analysis result in the ContentAnalysis table
        content_analysis_entry = ContentAnalysis.objects.create(
            sourceType='image',
            source_id=ocr_entry.ocr_id,
            isFlagged=True,
            severityLevel=severity,
            detectedLabels=detected_labels,
            analysisTime=datetime.now()
        )
        
        # Log the analysis result
        log_activity(current_user, 'Image Analysis', f'Analysis complete for image. Detected labels: {detected_labels}')

        recent_activities = ActivityLog.objects.filter(user=current_user).order_by('-timeStamp')[:10]
        
        return render(request, 'user_home.html', {
            'ocr_result': extracted_text,
            'image_label': detected_labels,
            'analysis_id': content_analysis_entry.analysis_id, # Pass the analysis ID
            'recent_activities': recent_activities,
        })
    return redirect('user_home')

def log_activity(user, activity_type, description):
    ActivityLog.objects.create(
        user=user,
        activityType=activity_type,
        description=description,
        timeStamp=datetime.now()
    )

def submit_feedback(request):
    if request.method == "POST":
        if not request.session.get('user_id'):
            messages.error(request, "You must be logged in to submit feedback.")
            return redirect('login_view')
        
        analysis_id = request.POST.get("analysis_id")
        correct_label = request.POST.get("correct_label")
        comments = request.POST.get("comments")

        try:
            current_user = User.objects.get(user_id=request.session['user_id'])
            content_analysis = ContentAnalysis.objects.get(analysis_id=analysis_id)
        except (User.DoesNotExist, ContentAnalysis.DoesNotExist):
            messages.error(request, "Invalid submission data. Please try again.")
            return redirect('user_dashboard')
        
        Feedback.objects.create(
            analysis=content_analysis,
            correctLabel=correct_label,
            comments=comments,
            submittedBy=current_user,
        )

        log_activity(current_user, 'Feedback Submitted', f'Feedback submitted for analysis ID {analysis_id}')
        messages.success(request, "Thank you for your feedback! It has been submitted successfully.")
        
    return redirect('user_dashboard')

from django.db.models import Count
from .models import TextContent, ActivityLog

@login_required
def generate_user_report(request):

    user_id = request.session.get('user_id')

    # 1. Get total submissions
    total_submissions = TextContent.objects.filter(user_id=user_id).count()

    # 2. Get total threats and their categories
    threat_submissions = TextContent.objects.filter(user_id=user_id).exclude(analysis_result='Not a threat')
    total_threats = threat_submissions.count()

    # Get threat categories and their counts
    threat_categories = threat_submissions.values('analysis_result').annotate(count=Count('analysis_result'))

    # Format the data for a clean display
    threat_categories_dict = {item['analysis_result']: item['count'] for item in threat_categories}

    # 3. Get recent activity logs for context
    recent_activity = ActivityLog.objects.filter(user_id=user_id).order_by('-timeStamp')[:10]

    report_data = {
        'total_submissions': total_submissions,
        'total_threats_detected': total_threats,
        'threat_categories': threat_categories_dict,
        'recent_activity': recent_activity
    }

    return render(request, 'user_report.html', {'report': report_data})