from django.urls import path
from .views import ClickResponseView

urlpatterns = [
    path('', ClickResponseView.as_view()),
]
