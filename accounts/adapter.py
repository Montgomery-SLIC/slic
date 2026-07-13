from allauth.account.adapter import DefaultAccountAdapter


class ResearcherAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        data = form.cleaned_data
        email = data.get('email', '')
        if email:
            user.email = email
        user.name = data.get('name', '')
        user.institution = data.get('institution', '')
        user.country = str(data.get('country', ''))
        user.faculty = data.get('faculty', '')
        user.research_level = data.get('research_level', '')
        user.funded = data.get('funded', False)
        user.mailing_list = data.get('mailing_list', False)
        if commit:
            user.save()
            # Mark invitation as used
            invitation = getattr(form, 'invitation', None)
            if invitation:
                invitation.used = True
                invitation.user = user
                invitation.save()
        return user
