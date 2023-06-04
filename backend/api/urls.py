from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('tags', views.TagsViewSet)
router.register('users', views.UserViewSet)
router.register('recipes', views.RecipeViewSet)
router.register('ingredients', views.IngredientsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
