from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, ActivityLikeViewSet, ActivitySaveViewSet, get_some_activities, like_activity, \
    unlike_activity, get_liked_activities, track_views

router = DefaultRouter()
router.register(r'activities', ActivityViewSet)
router.register(r'activity-likes', ActivityLikeViewSet)
router.register(r'activity-save', ActivitySaveViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('get-activities/', get_some_activities, name='get-activities'),
    path('like-activity/<str:activity_id>/', like_activity, name='like-activity'),
    path('unlike-activity/<str:activity_id>/', unlike_activity, name='unlike-activity'),
    path('liked-activities/', get_liked_activities, name='liked-activities'),
    path('track-views/', track_views, name='track-views')
]
