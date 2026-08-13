from django import forms
from slic.bootstrap_forms import BootstrapFormMixin
from .models import Experiment


class ExperimentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TermsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['terms']
        widgets = {'terms': forms.Textarea(attrs={'rows': 10})}
