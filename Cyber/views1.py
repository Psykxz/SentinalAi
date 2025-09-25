# Create your views here.
from datetime import datetime
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# def home(request):
#     return HttpResponse("Hello, Django World!")

# def sum(request):
#     s=0
#     for i in range(0,100):
#         s=s+1
#     return HttpResponse(f"Sum is {s}")

# def homepage(request):
#     return render(request, "homepage.html")

def homepage(request):
    role = request.session.get("role", "guest")
    username = request.session.get("username", "Guest")
    return render(request, "homepage.html", {"role": role, "username": username})

# app_name/views.py
from django.contrib import messages

from django.contrib.auth.hashers import make_password, check_password
from .models import User

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
            # return HttpResponse(f"Logged in as {user.username}, role: {request.session.get('role', 'not set')}")
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
        return redirect("login")  # block admins from accessing user home
    return render(request, "homepage.html",{"role": "user", "username": request.session.get("username", "User")})

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

        # Check password match
        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("register")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("register")

        # Save user
        User.objects.create(
            username=username,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            gender=gender,
            password=make_password(password1),  # hash password
            status=True
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")

    return render(request, "register.html")

# from django.shortcuts import render, redirect
# from .models import TextContent, ContentAnalysis
# from ml.utils import predict_text 

# def analyze_text(request):
#     if request.method == "POST":
#         user_text = request.POST.get("text_input")

#         # Save text input
#         text_entry = TextContent.objects.create(content=user_text)

#         # Run model prediction
#         label = predict_text(user_text)

#         # Save analysis result
#         ContentAnalysis.objects.create(
#             text_content=text_entry,
#             prediction=label
#         )

#         return render(request, "result.html", {"text": user_text, "label": label})

#     return render(request, "analyze_text.html")

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import TextContent, ContentAnalysis, User
from ml import utils

def analyze_text(request):
    if request.method == "POST":
        user_text = request.POST.get("text_input")
        if not user_text:
            return render(request, 'user_home.html', {'error': 'Text input cannot be empty.'})

        # 1. Get the current user
        # You need to ensure the user is logged in
        if not request.session.get('user_id'):
            return redirect('login_view')

        try:
            # Get the user object based on the session ID
            current_user = User.objects.get(user_id=request.session['user_id'])
        except User.DoesNotExist:
            return redirect('login_view')

        # 2. Store the original text in TextContent table
        text_entry = TextContent.objects.create(
            user=current_user,
            content=user_text,
            submission_time=datetime.now()
        )

        # 3. Analyze the text using the ML model
        analysis_result = utils.predict_text(user_text)
        detected_labels = analysis_result['label']
        # You may need to map the detected label to a severity level
        severity = "High" if "bullying" in detected_labels.lower() or "threat" in detected_labels.lower() else "Low"

        # 4. Store the analysis result in ContentAnalysis table
        ContentAnalysis.objects.create(
            sourceType='text',
            source_id=text_entry.text_id, # Link to the TextContent entry
            isFlagged=True, # Assuming any detection is flagged
            severityLevel=severity,
            detectedLabels=detected_labels,
            analysisTime=datetime.now()
        )

        return render(request, 'user_home.html', {
            'analysis_result': analysis_result, 
            'user_text': user_text,
            'label': detected_labels,  # Pass the detected label to the template
        })
    
    return redirect('user_home')

import pytesseract
# Replace 'C:\Path\To\Your\tesseract.exe' with the actual path to the tesseract.exe file on your computer.
pytesseract.pytesseract.tesseract_cmd = r'D:\OCR\tesseract.exe'

from PIL import Image
from .models import ImageContent, OCRResult, ContentAnalysis, User
import os

# Set the path to the Tesseract executable if needed (e.g., Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def analyze_image(request):
    if request.method == 'POST' and request.FILES.get('image_file'):
        uploaded_file = request.FILES['image_file']

        # 1. Get the current user
        if not request.session.get('user_id'):
            return redirect('login_view')

        try:
            current_user = User.objects.get(user_id=request.session['user_id'])
        except User.DoesNotExist:
            return redirect('login_view')

        # 2. Store the uploaded image details in the ImageContent table
        # NOTE: You will need to handle file saving to a media folder and get the file path
        # This is a simplified example. You would typically use Django's FileSystemStorage.
        image_path = os.path.join("media", uploaded_file.name)
        with open(image_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        image_entry = ImageContent.objects.create(
            user=current_user,
            filePath=image_path,
            upload_time=datetime.now()
        )

        # 3. Perform OCR to extract text from the image
        try:
            extracted_text = pytesseract.image_to_string(Image.open(uploaded_file))
        except Exception as e:
            return render(request, 'user_home.html', {'error': f'OCR failed: {e}'})
        
        if not extracted_text.strip():
            return render(request, 'user_home.html', {'ocr_result': 'No text detected in the image.'})

        # 4. Store the OCR result in the OCRResult table
        ocr_entry = OCRResult.objects.create(
            image_id=image_entry.image_id,  # Link to the ImageContent entry
            extractedText=extracted_text,
            extractionTime=datetime.now()
        )
        
        # 5. Analyze the extracted text using the ML model
        analysis_result = utils.predict_text(extracted_text)
        detected_labels = analysis_result['label']
        severity = "High" if "bullying" in detected_labels.lower() or "threat" in detected_labels.lower() else "Low"
        
        # 6. Store the analysis result in the ContentAnalysis table
        ContentAnalysis.objects.create(
            sourceType='image',
            source_id=ocr_entry.ocr_id, # Link to the OCRResult entry
            isFlagged=True,
            severityLevel=severity,
            detectedLabels=detected_labels,
            analysisTime=datetime.now()
        )
        
        # 7. Pass results to the template
        return render(request, 'user_home.html', {
            'ocr_result': extracted_text,
            'image_label': detected_labels,
        })
    
    return redirect('user_home')

# in your views.py file
# Make sure to import the functions from your new file
from ml.slang_processor import load_slang_from_db, replace_slang, replace_emojis

def process_content(text_content):
    # Load slang dictionary once (globally or within a class) to avoid
    # a database call on every request
    global slang_dict
    if 'slang_dict' not in globals():
        slang_dict = load_slang_from_db()
    
    # 1. Preprocess the text with the new module
    # First, replace emojis with their text descriptions
    processed_text = replace_emojis(text_content)
    
    # Then, replace slang with their meanings
    processed_text = replace_slang(processed_text, slang_dict)
    
    # 2. Use the processed text for prediction
    # ... your existing code to load and use the model
    # X = pd.Series([processed_text])
    # prediction = pipeline.predict(X)
    
    # ... rest of your code
    return processed_text, prediction # and the rest of the results

