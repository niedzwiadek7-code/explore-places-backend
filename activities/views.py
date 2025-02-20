from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from utils.decorators.timeit_decorator import timeit_decorator
from utils.geo_utils import Location
from .db_functions import annotate_with_distance
from .models import Entity as ActivityEntity, View as ActivityView, Like as ActivityLike, Save as ActivitySave, \
    Comment as ActivityComment
from .serializers import ActivitySerializer, ActivityLikeSerializer, ActivitySaveSerializer, \
    CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = ActivityComment.objects.all()
    serializer_class = CommentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        user = request.user
        activity_id = request.data.get('activity')
        activity = ActivityEntity.objects.get(id=activity_id)
        comment = request.data.get('comment')
        ActivityComment.objects.create(
            user=user,
            activity=activity,
            comment=comment
        )
        return Response({'message': 'Comment created'}, status=status.HTTP_201_CREATED)

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
@timeit_decorator
def get_some_activities(request):
    ignored_ids = request.data.get('ignored_ids', [])
    user_latitude = request.data.get('latitude')
    user_longitude = request.data.get('longitude')
    user_location = None

    count_to_get = int(request.query_params.get('count', 10))

    activities_viewed_ids = ActivityView.objects.filter(
        user=request.user,
        viewed=True
    ).values_list('activity_id', flat=True)

    all_excluded_ids = set(
        [int(id) for id in ignored_ids] + list(activities_viewed_ids)
    )

    queryset = ActivityEntity.objects.exclude(id__in=all_excluded_ids)

    if user_latitude is None or user_longitude is None:
        activities = queryset.order_by('?')[:count_to_get]
    else:
        user_location = Location(user_latitude, user_longitude)

        queryset = annotate_with_distance(
            queryset,
            user_location.latitude,
            user_location.longitude
        )

        activities = queryset.order_by('distance')[:count_to_get]

    bulk_list = []
    for activity in activities:
        bulk_list.append(
            ActivityView(
                user=request.user,
                activity=activity
            )
        )

    ActivityView.objects.bulk_create(bulk_list, ignore_conflicts=True)

    serializer = ActivitySerializer(activities, many=True, context={
        'request': request,
        'user_location': user_location
    })
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
    user_latitude = request.data.get('latitude')
    user_longitude = request.data.get('longitude')
    print(user_latitude, user_longitude)
    user_location = Location(user_latitude, user_longitude)

    liked_activity_ids = list(
        ActivityLike.objects.filter(user=user)
        .order_by('-created_at')
        .values_list('activity_id', flat=True)
    )

    activities_qs = ActivityEntity.objects.filter(id__in=liked_activity_ids)
    activities_qs = annotate_with_distance(activities_qs, user_location.latitude, user_location.longitude)

    activities = list(activities_qs)
    activities.sort(key=lambda a: liked_activity_ids.index(a.id))

    serializer = ActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes((JSONParser,))
@timeit_decorator
def track_views(request):
    activities = request.data.get('activityIds', [])

    activities_to_update = ActivityView.objects.filter(user=request.user, activity_id__in=activities)

    for activity in activities_to_update:
        activity.viewed = True

    ActivityView.objects.bulk_update(
        activities_to_update,
        ['viewed'],
    )

    return Response({'message': 'Activity saved'}, status=status.HTTP_200_OK)
