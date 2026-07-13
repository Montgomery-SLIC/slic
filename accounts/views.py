import secrets
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View, CreateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import logout
import rules

from .models import User, ResearcherInvitation
from .forms import ProfileEditForm


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        form = ProfileEditForm(user=user, initial={
            'email': user.email,
            'name': user.name,
            'institution': user.institution,
            'country': user.country,
            'faculty': user.faculty,
            'research_level': user.research_level,
            'funded': user.funded,
            'mailing_list': user.mailing_list,
        })
        return render(request, 'accounts/profile_edit.html', {'form': form})

    def post(self, request):
        form = ProfileEditForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            user.email = form.cleaned_data['email']
            user.name = form.cleaned_data['name']
            user.institution = form.cleaned_data['institution']
            user.country = str(form.cleaned_data['country'])
            user.faculty = form.cleaned_data['faculty']
            user.research_level = form.cleaned_data['research_level']
            user.funded = form.cleaned_data['funded']
            user.mailing_list = form.cleaned_data['mailing_list']
            new_password = form.cleaned_data.get('password')
            if new_password:
                user.set_password(new_password)
            user.save()
            messages.success(request, 'Your account has been updated successfully.')
            return redirect('accounts:profile_edit')
        return render(request, 'accounts/profile_edit.html', {'form': form})


class AccountDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been cancelled.')
        return redirect('account_login')


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin that enforces the accounts.admin_access rule"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not rules.test_rule('accounts.admin_access', request.user):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('experiments:index')
        return super().dispatch(request, *args, **kwargs)


class AdminUserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/admin_users.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        return User.objects.all().order_by('date_joined')


class AdminViewUserView(AdminRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/view_user.html'
    context_object_name = 'target'


class AdminSetAdminView(AdminRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        # Prevent removing own admin status
        if target == request.user:
            messages.error(request, 'You cannot change your own admin status.')
            return redirect('accounts:admin_view_user', pk=pk)
        target.admin = not target.admin
        target.is_staff = target.admin
        target.save(update_fields=['admin', 'is_staff'])
        status = 'granted' if target.admin else 'revoked'
        messages.success(request, f'Admin access {status}.')
        return redirect('accounts:admin_users')


class AdminDeleteUserView(AdminRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        if target == request.user:
            messages.error(request, 'You cannot delete your own account here.')
            return redirect('accounts:admin_users')
        target.delete()
        messages.success(request, 'User deleted.')
        return redirect('accounts:admin_users')


class ResearcherInvitationListView(AdminRequiredMixin, ListView):
    model = ResearcherInvitation
    template_name = 'accounts/researcher_invitations.html'
    context_object_name = 'invitations'
    ordering = ['-created_at']


class ResearcherInvitationCreateView(AdminRequiredMixin, View):
    def post(self, request):
        code = secrets.token_hex(8)
        ResearcherInvitation.objects.create(registration_code=code)
        messages.success(request, f'Invitation created: {code}')
        return redirect('accounts:invitations')

    def get(self, request):
        return redirect('accounts:invitations')


class ResearcherInvitationDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        invitation = get_object_or_404(ResearcherInvitation, pk=pk, used=False)
        invitation.delete()
        messages.success(request, 'Invitation deleted.')
        return redirect('accounts:invitations')
