from django.urls import path
from .views import RecipeRedirectView

urlpatterns = [
    path("r/<int:pk>/", RecipeRedirectView.as_view(), name="recipe-link"),
]
