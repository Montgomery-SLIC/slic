from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('settings/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('settings/cancel/', views.AccountDeleteView.as_view(), name='account_delete'),
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/users/<int:pk>/', views.AdminViewUserView.as_view(), name='admin_view_user'),
    path('admin/users/<int:pk>/set-admin/', views.AdminSetAdminView.as_view(), name='admin_set_admin'),
    path('admin/users/<int:pk>/delete/', views.AdminDeleteUserView.as_view(), name='admin_delete_user'),
    path('admin/invitations/', views.ResearcherInvitationListView.as_view(), name='invitations'),
    path('admin/invitations/new/', views.ResearcherInvitationCreateView.as_view(), name='invitation_create'),
    path('admin/invitations/<int:pk>/delete/', views.ResearcherInvitationDeleteView.as_view(), name='invitation_delete'),
]
