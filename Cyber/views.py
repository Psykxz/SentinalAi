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

pytesseract.pytesseract.tesseract_cmd = r'D:\OCR\tesseract.exe'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "D:\ROHIT MCA MINI PROJECT\myProject\ml\cyberbullying_model.pkl")

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

# def user_home(request):
#     user_id = request.session.get('user_id')
#     user_text_ids = TextContent.objects.filter(user_id=user_id).values_list('user_id', flat=True)
#     total_submissions = user_text_ids.count()
#     user_analysis_results = ContentAnalysis.objects.filter(source_id__in=user_text_ids)
#     total_threats = user_analysis_results.exclude(
#         detectedLabels='Not_cyberbullying'
#     ).count()
#     total_feedback_submitted = Feedback.objects.filter(submittedBy_id=user_id).count() 

#     recent_activities = ActivityLog.objects.filter(user_id=user_id).order_by('-timeStamp')[:5]

#     context = {
#         # The variables to make your summary cards dynamic
#         'total_submissions': total_submissions,
#         'total_threats_detected': total_threats,
#         'total_feedback_submitted': total_feedback_submitted,
        
#         # The list for the activity log section
#         'recent_activities': recent_activities,
#     }

#     if request.session.get("role") != "user":
#         return redirect("login")
#     return render(request, "user_home.html",{"role": "user", "username": request.session.get("username", "User")}, context)



# def user_home(request):
#     user_id = request.session.get('user_id')
    
#     if request.session.get("role") != "user":
#         return redirect("login")

#     # 1. FIX: Retrieve TextContent PKs ('id'), NOT 'user_id's, to link to ContentAnalysis
#     # This retrieves the list of IDs for submissions belonging to the user.
#     user_text_ids = TextContent.objects.filter(user_id=user_id).values_list('user_id', flat=True)
#     total_submissions = user_text_ids.count()
    
#     # 2. Total Threats
#     user_analysis_results = ContentAnalysis.objects.filter(source_id__in=user_text_ids)
#     total_threats = user_analysis_results.exclude(
#         detectedLabels='Not_cyberbullying'
#     ).count()
    
#     # 3. Total Feedback
#     total_feedback_submitted = Feedback.objects.filter(submittedBy_id=user_id).count() 

#     # 4. Recent Activities
#     recent_activities = ActivityLog.objects.filter(user_id=user_id).order_by('-timeStamp')[:5]

#     # 5. FIX: Merge ALL context variables into a single dictionary
#     context = {
#         # Summary cards data
#         'total_submissions': total_submissions,
#         'total_threats_detected': total_threats,
#         'total_feedback_submitted': total_feedback_submitted,
        
#         # Activity log data
#         'recent_activities': recent_activities,
        
#         # Session/Auth data
#         "role": "user", 
#         "username": request.session.get("username", "User")
        
#         # NOTE: Add any other context variables needed by user_home.html here!
#     }

#     # 6. FIX: Call render with a single, merged context dictionary
#     return render(request, "user_home.html", context)


from django.contrib.contenttypes.models import ContentType

def user_home(request):
    user_id = request.session.get('user_id')
    
    if request.session.get("role") != "user":
        return redirect("login")

    user_text_pks = TextContent.objects.filter(user_id=user_id).values_list('text_id', flat=True)
    total_submissions = user_text_pks.count()
    
    text_content_type = ContentType.objects.get_for_model(TextContent)

    user_analysis_results = ContentAnalysis.objects.filter(
        content_type=text_content_type, 
        object_id__in=user_text_pks  
    )
    
    total_threats = user_analysis_results.exclude(
        detectedLabels='Not_cyberbullying'
    ).count()
    
    total_feedback_submitted = Feedback.objects.filter(submittedBy_id=user_id).count() 

    recent_activities = ActivityLog.objects.filter(user_id=user_id).order_by('-timeStamp')[:5]

    context = {
        'total_submissions': total_submissions,
        'total_threats_detected': total_threats,
        'total_feedback_submitted': total_feedback_submitted,
        
        'recent_activities': recent_activities,
        
        "role": "user", 
        "username": request.session.get("username", "User")
        
    }

    return render(request, "user_home.html", context)

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

        log_activity(current_user, 'Text Submission', f'Submitted text for analysis: "{user_text[:50]}..."')

        processed_text = replace_emojis(user_text)
        if slang_dict:
            processed_text = replace_slang(processed_text, slang_dict)

        text_entry = TextContent.objects.create(
            user=current_user,
            content=user_text,
            submission_time=datetime.now()
        )

        analysis_result = utils.predict_text(processed_text)
        detected_labels = analysis_result['label']
        severity = "High" if "bullying" in detected_labels.lower() or "threat" in detected_labels.lower() else "Low"

        content_analysis_entry = ContentAnalysis.objects.create(
            sourceType='text',
            source_object=text_entry,
            isFlagged=True,
            severityLevel=severity,
            detectedLabels=detected_labels,
            analysisTime=datetime.now()
        )

        log_activity(current_user, 'Text Analysis', f'Analysis complete. Detected labels: {detected_labels}')

        recent_activities = ActivityLog.objects.filter(user=current_user).order_by('-timeStamp')[:10]

        return render(request, 'user_home.html', {
            'analysis_result': analysis_result,
            'user_text': user_text,
            'label': detected_labels,
            'analysis_id': content_analysis_entry.analysis_id,
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

        processed_text = replace_emojis(extracted_text)
        if slang_dict:
            processed_text = replace_slang(processed_text, slang_dict)

        ocr_entry = OCRResult.objects.create(
            image=image_entry,
            extractedText=extracted_text,
            extractionTime=datetime.now()
        )
        
        analysis_result = utils.predict_text(processed_text)
        detected_labels = analysis_result['label']
        severity = "High" if "bullying" in detected_labels.lower() or "threat" in detected_labels.lower() else "Low"
        
        content_analysis_entry = ContentAnalysis.objects.create(
        sourceType='image',
        source_object=ocr_entry, 
        isFlagged=True,
        severityLevel=severity,
        detectedLabels=detected_labels,
        analysisTime=datetime.now()
       )
        
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
from .models import TextContent, ActivityLog, ContentAnalysis
from django.contrib.contenttypes.models import ContentType

def generate_user_report(request):

    user_id = request.session.get('user_id')

    user_text_pks = TextContent.objects.filter(user_id=user_id).values_list('text_id', flat=True)
    total_submissions = user_text_pks.count()

    text_content_type = ContentType.objects.get_for_model(TextContent)

    user_analysis_results = ContentAnalysis.objects.filter(
        content_type=text_content_type, 
        object_id__in=user_text_pks    
    )

    threat_submissions = user_analysis_results.exclude(
        detectedLabels='Not_cyberbullying'
    )
    total_threats = threat_submissions.count()

    threat_categories = threat_submissions.values('detectedLabels').annotate(
        count=Count('detectedLabels')
    ).order_by('-count')

    threat_categories_dict = {
        item['detectedLabels']: item['count'] 
        for item in threat_categories
    }

    recent_activity = ActivityLog.objects.filter(user_id=user_id).order_by('-timeStamp')[:10]

    # report_data = {
    #     'total_submissions': total_submissions,
    #     'total_threats_detected': total_threats,
    #     'threat_categories': threat_categories_dict,
    #     'recent_activity': recent_activity
    # }

    # return render(request, 'user_report.html', {'report': report_data})

    if total_submissions > 0:
        threat_percentage = round((total_threats / total_submissions) * 100)
        safe_submissions = total_submissions - total_threats
    else:
        threat_percentage = 0
        safe_submissions = 0

    report_data = {
        'total_submissions': total_submissions,
        'total_threats_detected': total_threats,
        'threat_categories': threat_categories_dict,
        'recent_activity': recent_activity,
        # New metrics to pass to the template
        'safe_submissions': safe_submissions, 
        'threat_percentage': threat_percentage, 
        'current_time': datetime.now(), 
    }

    return render(request, 'user_report.html', {'report': report_data})



import csv
import io
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect
# Import WeasyPrint for PDF generation (if installed)
try:
    from weasyprint import HTML
except ImportError:
    HTML = None 
    print("Warning: WeasyPrint not installed. PDF export will be disabled.")


# Reuse the logic from generate_user_report to get report_data
# NOTE: You MUST replace this with your actual data retrieval logic.
def get_report_data_for_user(user_id):
    # This function should contain the exact data fetching/calculation
    # logic currently in your generate_user_report view.
    
    # Placeholder implementation (REPLACE THIS)
    from .models import TextContent, ContentAnalysis, ActivityLog # Replace with your actual imports
    from django.db.models import Count
    from django.contrib.contenttypes.models import ContentType
    
    user_text_pks = TextContent.objects.filter(user_id=user_id).values_list('text_id', flat=True)
    total_submissions = user_text_pks.count()
    text_content_type = ContentType.objects.get_for_model(TextContent)
    
    user_analysis_results = ContentAnalysis.objects.filter(
        content_type=text_content_type, 
        object_id__in=user_text_pks    
    )
    
    threat_submissions = user_analysis_results.exclude(detectedLabels='Not_cyberbullying')
    total_threats = threat_submissions.count()

    if total_submissions > 0:
        threat_percentage = round((total_threats / total_submissions) * 100)
    else:
        threat_percentage = 0
        
    threat_categories_dict = {
        item['detectedLabels']: item['count'] 
        for item in threat_submissions.values('detectedLabels').annotate(count=Count('detectedLabels'))
    }
    
    recent_activity = ActivityLog.objects.filter(user_id=user_id).order_by('-timeStamp')[:10]

    return {
        'total_submissions': total_submissions,
        'total_threats_detected': total_threats,
        'threat_categories': threat_categories_dict,
        'recent_activity': recent_activity,
        'threat_percentage': threat_percentage,
        'current_time': datetime.now(),
    }


# @login_required
def download_report(request, report_format):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
        
    report_data = get_report_data_for_user(user_id)
    
    if report_format == 'excel':
        # --- EXCEL/CSV GENERATION ---
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sentinelai_report_{user_id}.csv"'

        writer = csv.writer(response)

        # 1. Write Summary Stats
        writer.writerow(['Report Summary'])
        writer.writerow(['Total Submissions', 'Total Threats', 'Threat Rate (%)'])
        writer.writerow([report_data['total_submissions'], report_data['total_threats_detected'], report_data['threat_percentage']])
        writer.writerow([])
        
        # 2. Write Threat Categories
        writer.writerow(['Threat Categories'])
        writer.writerow(['Category', 'Count'])
        for category, count in report_data['threat_categories'].items():
            # Use the replace_chars logic here manually if you need cleaning
            clean_category = category.replace('_', ' ').title() 
            writer.writerow([clean_category, count])
        writer.writerow([])
        
        # 3. Write Recent Activity (Detailed logs are often most useful in Excel)
        writer.writerow(['Recent Activity Logs'])
        writer.writerow(['Timestamp', 'Activity Type', 'Description'])
        for activity in report_data['recent_activity']:
            writer.writerow([
                activity.timeStamp.strftime("%Y-%m-%d %H:%M:%S"), 
                activity.activityType, 
                activity.description
            ])

        return response
        
    elif report_format == 'pdf' and HTML:
        # --- PDF GENERATION (Requires WeasyPrint) ---
        
        html_content = render_to_string('pdf_report_template.html', {'report': report_data, 'user_id': user_id})
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sentinelai_report_{user_id}.pdf"'

        # Generate PDF using WeasyPrint
        HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(response)
        
        return response
        
    else:
        # Fallback for unsupported format or missing PDF library
        return HttpResponse("Report format not supported or PDF library missing.", status=400)