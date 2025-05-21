from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"ingredients", IngredientViewSet)
router.register(r"recipes", RecipeViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
