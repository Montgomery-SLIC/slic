from django.urls import path
from . import views

app_name = 'experiments'
urlpatterns = [
    path('', views.ExperimentListView.as_view(), name='index'),
    path('new/', views.ExperimentCreateView.as_view(), name='new'),
    path('<int:pk>/', views.ExperimentDetailView.as_view(), name='show'),
    path('<int:pk>/edit/', views.ExperimentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ExperimentDeleteView.as_view(), name='delete'),
    path('<int:pk>/download/', views.ExperimentDownloadView.as_view(), name='download'),
    path('<int:pk>/complete/', views.ExperimentCompleteView.as_view(), name='complete'),
    path('<int:pk>/terms/', views.ExperimentTermsView.as_view(), name='terms'),
]
