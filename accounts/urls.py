from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import UserViewSet, CustomTokenObtainPairView, CustomTokenRefreshView, SendVerificationCode, \
    verify_verification_code

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('send-verification-code/', SendVerificationCode.as_view(), name='send-verification-code'),
    path('verify-code/', verify_verification_code, name='verify-code'),
]
