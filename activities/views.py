from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .models import Entity as ActivityEntity, View as ActivityView, Like as ActivityLike, Save as ActivitySave
from .serializers import ActivitySerializer, ActivityLikeSerializer, ActivitySaveSerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = ActivityEntity.objects.all()
    serializer_class = ActivitySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['POST'])
def like_activity(request, activity_id):
    activity = ActivityEntity.objects.get(id=activity_id)
    ActivityLike.objects.create(
        user=request.user,
        activity=activity
    )
    return Response({'message': 'Activity liked'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def unlike_activity(request, activity_id):
    activity = ActivityEntity.objects.get(id=activity_id)
    ActivityLike.objects.filter(user=request.user, activity=activity).delete()
    return Response({'message': 'Activity unliked'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes((JSONParser,))
def get_some_activities(request):
    user_latitude = request.data.get('latitude')
    user_longitude = request.data.get('longitude')

    count_to_get = int(request.query_params.get('count', 10))

    activities_viewed = ActivityView.objects.filter(user=request.user)
    activities_viewed_ids = [activity_view.activity.id for activity_view in activities_viewed]

    if user_latitude is None or user_longitude is None:
        activities = ActivityEntity.objects.exclude(id__in=activities_viewed_ids).order_by('?')[:count_to_get]
    else:
        user_location = Point(float(user_longitude), float(user_latitude), srid=4326)

        activities = ActivityEntity.objects.exclude(id__in=activities_viewed_ids).annotate(
            distance=Distance('point_field', user_location)
        ).order_by('distance')[:count_to_get]

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


@api_view(['POST'])
def get_liked_activities(request):
    user = request.user
    liked_activities = ActivityLike.objects.filter(user=user).select_related('activity').order_by('-created_at')
    activities = [like.activity for like in liked_activities]
    serializer = ActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes((JSONParser,))
def track_views(request):
    activities = request.data.get('activityIds', [])

    for activity_id in activities:
        ActivityView.objects.update(
            user=request.user,
            activity=ActivityEntity.objects.get(id=activity_id),
            viewed=True
        )

    return Response({'message': 'Activity saved'}, status=status.HTTP_200_OK)
