from django import forms
from .models import User, Show

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password']

class ShowForm(forms.ModelForm):
    class Meta:
        model = Show
        fields = ['title', 'description', 'date', 'location', 'price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
