from django import forms


_SKIP_WIDGETS = (
    forms.CheckboxInput,
    forms.CheckboxSelectMultiple,
    forms.HiddenInput,
    forms.FileInput,
    forms.MultipleHiddenInput,
)


def apply_form_control(form):
    for field in form.fields.values():
        if isinstance(field.widget, _SKIP_WIDGETS):
            continue
        existing = field.widget.attrs.get('class', '')
        if 'form-control' not in existing:
            field.widget.attrs['class'] = (existing + ' form-control').strip()


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control(self)
