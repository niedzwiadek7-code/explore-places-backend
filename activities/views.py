from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User, Activity
from .serializers import UserSerializer, ActivitySerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class SendLoginEmailView(APIView):
    def post(self, request):
        email = request.data.get('email')
        user = User.objects.get(email=email)
        if user:
            token = urlsafe_base64_encode(force_bytes(user.username))
            login_url = request.build_absolute_uri(
                reverse('login-confirm', kwargs={'token': token})
            )
            send_mail(
                'Login to Travel App',
                f'Click here to login: {login_url}',
                'travelapp123@outlook.com',
                [email],
                fail_silently=False
            )

            return Response({'message': 'Email sent'}, status=status.HTTP_200_OK)

        return Response({'message': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)

class LoginConfirmView(APIView):
    def get(self, request, token):
        try:
            user_username = force_str(urlsafe_base64_decode(token))
            user = User.objects.get(username=user_username)
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({'message': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError):
            return Response({'message': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

