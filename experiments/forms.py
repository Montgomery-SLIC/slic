from django import forms
from .models import Experiment


class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TermsForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['terms']
        widgets = {'terms': forms.Textarea(attrs={'rows': 10})}
