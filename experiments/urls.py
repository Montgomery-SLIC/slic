from django.urls import path
from . import views, preview

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
    # Preview
    path('<int:pk>/preview/', preview.PreviewHomeView.as_view(), name='preview_home'),
    path('<int:pk>/preview/start/', preview.PreviewStartView.as_view(), name='preview_start'),
    path('<int:pk>/preview/sample/<int:sample_id>/', preview.PreviewSampleView.as_view(), name='preview_sample'),
    path('<int:pk>/preview/task/<int:task_id>/', preview.PreviewTaskView.as_view(), name='preview_task'),
    path('<int:pk>/preview/finish/', preview.PreviewFinishView.as_view(), name='preview_finish'),
    path('<int:pk>/preview/audio/<int:sample_task_id>/', preview.preview_audio, name='preview_audio'),
]
