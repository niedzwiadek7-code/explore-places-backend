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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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

@api_view(['POST'])
def like_activity(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    ActivityLike.objects.create(
        user=request.user,
        activity=activity
    )
    return Response({'message': 'Activity liked'}, status=status.HTTP_200_OK)

def unlike_activity(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    ActivityLike.objects.filter(user=request.user, activity=activity).delete()
    return Response({'message': 'Activity unliked'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_some_activities(request):
    count_to_get = int(request.query_params.get('count', 10))
    activities_viewed = ActivityView.objects.filter(user=request.user)
    activities_viewed_ids = [activity_view.activity.id for activity_view in activities_viewed]
    activities = Activity.objects.exclude(id__in=activities_viewed_ids)[:count_to_get]

    for activity in activities:
        ActivityView.objects.create(
            user=request.user,
            activity=activity
        )

    serializer = ActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

class ActivityLikeViewSet(viewsets.ModelViewSet):
    queryset = ActivityLike.objects.all()
    serializer_class = ActivityLikeSerializer

class ActivitySaveViewSet(viewsets.ModelViewSet):
    queryset = ActivitySave.objects.all()
    serializer_class = ActivitySaveSerializer

@api_view(['GET'])
def get_liked_activities(request):
    user = request.user
    liked_activities = ActivityLike.objects.filter(user=user).select_related('activity')
    activities = [like.activity for like in liked_activities]
    serializer = ActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
