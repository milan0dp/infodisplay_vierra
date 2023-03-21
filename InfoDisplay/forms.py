from django import forms
from django.forms import ClearableFileInput
from .models import upload_file


class ResumeUpload(forms.ModelForm):
    class Meta:
        model = upload_file
        fields = ['data']
        widgets = {
            'data': ClearableFileInput(attrs={'multiple': True}),
        }
