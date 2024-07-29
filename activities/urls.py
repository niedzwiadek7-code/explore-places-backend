from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ActivityViewSet, ActivityLikeViewSet, ActivitySaveViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'activities', ActivityViewSet)
router.register(r'activity-likes', ActivityLikeViewSet)
router.register(r'activity-save', ActivitySaveViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
