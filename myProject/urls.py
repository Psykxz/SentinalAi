from django.contrib import admin
from django.urls import path

from Cyber.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", homepage, name="homepage"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("admin_login/", login_view, name="admin_login"),
    path("admin_dashboard/", admin_dashboard, name="admin_dashboard"),
    path("user_home/", user_home, name="user_home"),
    path("user_dashboard/",user_dashboard,name="user_dashboard"),
    path("analyze-text/", analyze_text, name="analyze_text"),
    path('analyze_image/', analyze_image, name='analyze_image'),
    path('submit-feedback/', submit_feedback, name='submit_feedback'),
    path('generate_user_report/', generate_user_report, name='generate_user_report'),
    path('report/download/<str:report_format>/', download_report, name='download_report'),
]