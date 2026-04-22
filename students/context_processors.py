from .forms import PreRegistrationForm


def pre_registration_form(request):
    return {
        'pre_registration_form': PreRegistrationForm(),
    }
