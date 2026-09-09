from django import forms

from .models import UserSettings


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['currency', 'initial_balance']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['currency'].widget.attrs['class'] = 'form-select'
        self.fields['initial_balance'].widget.attrs['class'] = 'form-control'
