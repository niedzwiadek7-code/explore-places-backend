from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from travel_app_backend import settings
from .models import User, Activity, VerificationCode, ActivityView, ActivityLike, ActivitySave
from .serializers import UserSerializer, ActivitySerializer, ActivityLikeSerializer, ActivitySaveSerializer


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

class SendVerificationCode(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)

            try:
                verification_code = VerificationCode.objects.get(user=user)
                code = verification_code.code
            except VerificationCode.DoesNotExist:
                code = get_random_string(length=6, allowed_chars='0123456789')
                VerificationCode.objects.create(user=user, code=code)

            send_mail(
                'Verification Code',
                f'Your verification code is: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )

            return Response({'message': 'Email sent'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_verification_code(request):
    email = request.data.get('email')
    code = request.data.get('code')

    try:
        verification_code = VerificationCode.objects.get(user__email=email, code=code)
        user = verification_code.user
        user.email_verified = True
        user.save()
        verification_code.delete()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    except VerificationCode.DoesNotExist:
        return Response({'message': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_some_activities(request):
    activities_viewed = ActivityView.objects.filter(user=request.user)
    activities_viewed_ids = [activity_view.activity.id for activity_view in activities_viewed]
    activities = Activity.objects.exclude(id__in=activities_viewed_ids)[:10]

    for activity in activities:
        ActivityView.objects.create(
            user=request.user,
            activity=activity
        )

    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

class ActivityLikeViewSet(viewsets.ModelViewSet):
    queryset = ActivityLike.objects.all()
    serializer_class = ActivityLikeSerializer

class ActivitySaveViewSet(viewsets.ModelViewSet):
    queryset = ActivitySave.objects.all()
    serializer_class = ActivitySaveSerializer
