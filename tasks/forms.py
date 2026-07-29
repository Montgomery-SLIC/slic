from django import forms
from .models import (
    QuestionTask, SampleTask, ListeningTask, ClickTask, IntermediateScreenTask,
    Question, Option, Scale,
)


class QuestionTaskForm(forms.ModelForm):
    class Meta:
        model = QuestionTask
        fields = ['name']


class SampleTaskForm(forms.ModelForm):
    class Meta:
        model = SampleTask
        fields = ['name', 'calibration']


class ListeningTaskForm(forms.ModelForm):
    class Meta:
        model = ListeningTask
        fields = ['name', 'listens']


class ClickTaskForm(forms.ModelForm):
    class Meta:
        model = ClickTask
        fields = ['name', 'prompt', 'explanation_prompt']
        widgets = {
            'prompt': forms.Textarea(attrs={'rows': 3}),
            'explanation_prompt': forms.Textarea(attrs={'rows': 3}),
        }


class IntermediateScreenTaskForm(forms.ModelForm):
    class Meta:
        model = IntermediateScreenTask
        fields = ['name', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 6})}


class AudioUploadForm(forms.Form):
    audio = forms.FileField(label='Audio file')

    def clean_audio(self):
        f = self.cleaned_data['audio']
        if f.size >= 314572800:
            raise forms.ValidationError('File must be under 300 MB.')
        return f


class TranscriptUploadForm(forms.Form):
    transcript = forms.FileField(label='Transcript file')

    def clean_transcript(self):
        f = self.cleaned_data['transcript']
        if f.size >= 314572800:
            raise forms.ValidationError('File must be under 300 MB.')
        return f


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'prompt', 'required']
        widgets = {'prompt': forms.Textarea(attrs={'rows': 3})}


class QuestionPromptForm(forms.ModelForm):
    """Inline edit form for an existing question - type is immutable after creation."""
    class Meta:
        model = Question
        fields = ['prompt', 'required']
        widgets = {'prompt': forms.Textarea(attrs={'rows': 2, 'class': 'form-control form-control-sm'})}


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['contents']


class ScaleForm(forms.ModelForm):
    class Meta:
        model = Scale
        fields = ['bins', 'low', 'high']
