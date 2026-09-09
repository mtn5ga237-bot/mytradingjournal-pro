from django import forms
from django.conf import settings

from .models import Trade


class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = [
            'date_ouverture', 'date_fermeture', 'paire', 'direction', 'taille',
            'strategie', 'session', 'prix_entree', 'prix_sortie', 'stop_loss',
            'take_profit', 'resultat_pips', 'resultat_monetaire', 'commission_swap',
            'humeur_avant', 'humeur_apres', 'respect_plan', 'commentaires', 'screenshot',
        ]
        widgets = {
            'date_ouverture': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fermeture': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'commentaires': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Notes, contexte, leçons…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (existing + ' form-check-input').strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = (existing + ' form-control').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean_screenshot(self):
        image = self.cleaned_data.get('screenshot')
        if image and hasattr(image, 'size') and image.size > settings.MAX_SCREENSHOT_SIZE:
            raise forms.ValidationError("L'image dépasse la taille maximale autorisée (5 Mo).")
        return image
