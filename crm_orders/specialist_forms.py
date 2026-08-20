from django import forms

from .specialist import SECTIONS


class SpecialistDiscoveryForm(forms.Form):
    def __init__(self, *args, section_key, **kwargs):
        self.section_key = section_key
        super().__init__(*args, **kwargs)
        section = next(item for item in SECTIONS if item[0] == section_key)
        for key, question, help_text in section[3]:
            self.fields[key] = forms.CharField(label=question, help_text=help_text, min_length=10, max_length=4000, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "پاسخ خود را با مثال واقعی بنویسید..."}))
