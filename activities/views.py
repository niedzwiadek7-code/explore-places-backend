from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Activity, ActivityView, ActivityLike, ActivitySave
from .serializers import ActivitySerializer, ActivityLikeSerializer, ActivitySaveSerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


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
    liked_activities = ActivityLike.objects.filter(user=user).select_related('activity').order_by('-created_at')
    activities = [like.activity for like in liked_activities]
    serializer = ActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
