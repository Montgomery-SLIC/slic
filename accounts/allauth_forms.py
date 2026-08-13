from allauth.account.forms import LoginForm, SignupForm
from slic.bootstrap_forms import apply_form_control


class SLICLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control(self)


class SLICSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control(self)
