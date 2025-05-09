from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Show

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'user_type',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            # Password fields will inherit from UserCreationForm, we can override if needed
            # For example, to add placeholders or classes to password fields:
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}), 
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('user_type') in ['admin', 'organizer']:
            user.is_staff = True
        if commit:
            user.save()
        return user

    # If you need to add custom cleaning for email or user_type, you can do it here.
    # For example, to make email required (though AbstractUser usually has it as required):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['email'].required = True

class ShowForm(forms.ModelForm):
    class Meta:
        model = Show
        fields = ['title', 'description', 'image', 'date', 'location', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'})
        }
