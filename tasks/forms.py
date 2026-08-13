from django import forms
from django.utils.translation import gettext_lazy as _
from slic.bootstrap_forms import BootstrapFormMixin
from .models import (
    QuestionTask, SampleTask, ListeningTask, ClickTask, IntermediateScreenTask,
    Question, Option, Scale,
)


class QuestionTaskForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = QuestionTask
        fields = ['name']


class SampleTaskForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SampleTask
        fields = ['name', 'calibration']


class ListeningTaskForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ListeningTask
        fields = ['name', 'listens']


class ClickTaskForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ClickTask
        fields = ['name', 'prompt', 'explanation_prompt']
        widgets = {
            'prompt': forms.Textarea(attrs={'rows': 3}),
            'explanation_prompt': forms.Textarea(attrs={'rows': 3}),
        }


class IntermediateScreenTaskForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = IntermediateScreenTask
        fields = ['name', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 6})}


class AudioUploadForm(BootstrapFormMixin, forms.Form):
    audio = forms.FileField(label=_('Audio file'))

    def clean_audio(self):
        f = self.cleaned_data['audio']
        if f.size >= 314572800:
            raise forms.ValidationError(_('File must be under 300 MB.'))
        return f


class TranscriptUploadForm(BootstrapFormMixin, forms.Form):
    transcript = forms.FileField(label=_('Transcript file'))

    def clean_transcript(self):
        f = self.cleaned_data['transcript']
        if f.size >= 314572800:
            raise forms.ValidationError(_('File must be under 300 MB.'))
        if not f.name.lower().endswith(('.eaf', '.xml')):
            raise forms.ValidationError(_('Transcript must be an EAF file (.eaf or .xml).'))
        return f


class QuestionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'prompt', 'required']
        widgets = {'prompt': forms.Textarea(attrs={'rows': 3})}


class QuestionPromptForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ['prompt', 'required']
        widgets = {'prompt': forms.Textarea(attrs={'rows': 2, 'class': 'form-control form-control-sm'})}


class OptionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Option
        fields = ['contents']


class ScaleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Scale
        fields = ['bins', 'low', 'high']

    def clean(self):
        cleaned_data = super().clean()
        bins = cleaned_data.get('bins')
        low = cleaned_data.get('low', '')
        high = cleaned_data.get('high', '')
        if bins and low and high:
            try:
                low_num = float(low)
                high_num = float(high)
                if high_num <= low_num:
                    self.add_error('high', _('High value must be greater than low value.'))
                elif bins > int(high_num - low_num) + 1:
                    self.add_error(
                        'bins',
                        _('Number of options (%(bins)s) cannot exceed the numeric range %(low)s-%(high)s.')
                        % {'bins': bins, 'low': low, 'high': high},
                    )
            except (ValueError, TypeError):
                pass
        return cleaned_data
