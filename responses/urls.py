from django.urls import path
from . import views

app_name = 'responses'
urlpatterns = [
    path('<slug:slug>/home/', views.ExperimentHomeView.as_view(), name='home'),
    path('<slug:slug>/start/', views.ExperimentStartView.as_view(), name='start'),
    path('<slug:slug>/<int:participant_id>/sample/<int:sample_id>/', views.SampleIntroView.as_view(), name='sample_intro'),
    path('<slug:slug>/<int:participant_id>/<str:task_type>/<int:task_id>/', views.TaskView.as_view(), name='task_view'),
    path('<slug:slug>/<int:participant_id>/<str:task_type>/<int:task_id>/submit/', views.TaskSubmitView.as_view(), name='task_submit'),
    path('<slug:slug>/<int:participant_id>/finish/', views.FinishView.as_view(), name='finish'),
    path('audio/<int:sample_task_id>/', views.serve_audio, name='serve_audio'),
]
