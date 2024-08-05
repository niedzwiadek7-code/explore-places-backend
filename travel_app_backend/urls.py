"""
URL configuration for travel_app_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from activities.views import CustomTokenObtainPairView, CustomTokenRefreshView, SendVerificationCode, \
    verify_verification_code, get_some_activities, like_activity, unlike_activity

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('activities.urls')),
    path('api/token', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/send-verification-code/', SendVerificationCode.as_view(), name='send-verification-code'),
    path('api/verify-code/', verify_verification_code, name='verify-code'),
    path('api/get-activities/', get_some_activities, name='get-activities'),
    path('api/like-activity/<str:activity_id>/', like_activity, name='like-activity'),
    path('api/unlike-activity/<str:activity_id>/', unlike_activity, name='unlike-activity'),
]
