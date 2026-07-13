from django.urls import path
from . import views

app_name = 'tasks'
urlpatterns = [
    # QuestionTask
    path('<str:taskable_type>/<int:taskable_id>/question-task/new/', views.question_task_new, name='question_task_new'),
    path('<str:taskable_type>/<int:taskable_id>/question-task/', views.question_task_create, name='question_task_create'),
    path('question-task/<int:pk>/edit/', views.question_task_edit, name='question_task_edit'),
    path('question-task/<int:pk>/update/', views.question_task_update, name='question_task_update'),
    path('question-task/<int:pk>/delete/', views.question_task_delete, name='question_task_delete'),

    # SampleTask
    path('<str:taskable_type>/<int:taskable_id>/sample-task/new/', views.sample_task_new, name='sample_task_new'),
    path('<str:taskable_type>/<int:taskable_id>/sample-task/', views.sample_task_create, name='sample_task_create'),
    path('sample-task/<int:pk>/edit/', views.sample_task_edit, name='sample_task_edit'),
    path('sample-task/<int:pk>/update/', views.sample_task_update, name='sample_task_update'),
    path('sample-task/<int:pk>/delete/', views.sample_task_delete, name='sample_task_delete'),
    path('sample-task/<int:pk>/audio/', views.audio_upload, name='audio_upload'),
    path('sample-task/<int:pk>/audio/delete/', views.audio_delete, name='audio_delete'),
    path('sample-task/<int:pk>/transcript/', views.transcript_upload, name='transcript_upload'),
    path('sample-task/<int:pk>/transcript/delete/', views.transcript_delete, name='transcript_delete'),
    path('sample-task/<int:pk>/calibration/', views.calibration_toggle, name='calibration_toggle'),

    # ListeningTask
    path('<str:taskable_type>/<int:taskable_id>/listening-task/new/', views.listening_task_new, name='listening_task_new'),
    path('<str:taskable_type>/<int:taskable_id>/listening-task/', views.listening_task_create, name='listening_task_create'),
    path('listening-task/<int:pk>/edit/', views.listening_task_edit, name='listening_task_edit'),
    path('listening-task/<int:pk>/update/', views.listening_task_update, name='listening_task_update'),
    path('listening-task/<int:pk>/delete/', views.listening_task_delete, name='listening_task_delete'),

    # ClickTask
    path('<str:taskable_type>/<int:taskable_id>/click-task/new/', views.click_task_new, name='click_task_new'),
    path('<str:taskable_type>/<int:taskable_id>/click-task/', views.click_task_create, name='click_task_create'),
    path('click-task/<int:pk>/edit/', views.click_task_edit, name='click_task_edit'),
    path('click-task/<int:pk>/update/', views.click_task_update, name='click_task_update'),
    path('click-task/<int:pk>/delete/', views.click_task_delete, name='click_task_delete'),

    # IntermediateScreenTask
    path('<str:taskable_type>/<int:taskable_id>/intermediate-screen/new/', views.intermediate_screen_new, name='intermediate_screen_new'),
    path('<str:taskable_type>/<int:taskable_id>/intermediate-screen/', views.intermediate_screen_create, name='intermediate_screen_create'),
    path('intermediate-screen/<int:pk>/edit/', views.intermediate_screen_edit, name='intermediate_screen_edit'),
    path('intermediate-screen/<int:pk>/update/', views.intermediate_screen_update, name='intermediate_screen_update'),
    path('intermediate-screen/<int:pk>/delete/', views.intermediate_screen_delete, name='intermediate_screen_delete'),

    # Common
    path('task/<int:pk>/random/', views.task_random, name='task_random'),

    # Questions
    path('question-task/<int:qt_pk>/questions/', views.question_create, name='question_create'),
    path('questions/<int:pk>/update/', views.question_update, name='question_update'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('questions/<int:pk>/scale/', views.scale_update, name='scale_update'),

    # Options
    path('questions/<int:q_pk>/options/', views.option_create, name='option_create'),
    path('options/<int:pk>/delete/', views.option_delete, name='option_delete'),
]
