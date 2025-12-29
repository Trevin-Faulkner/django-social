from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Experience, Message, User


class SignupForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'role',
            'password1',
            'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            base_classes = 'w-full mt-1 rounded-xl border border-slate-200 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500'
            if isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'space-y-2 mt-2'})
            else:
                field.widget.attrs.update({'class': base_classes})


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'headline',
            'bio',
            'skills',
            'goals',
            'location',
            'profile_image',
            'membership_plan',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'goals': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    'class': 'w-full rounded-xl border border-slate-200 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500',
                }
            )
        self.fields['profile_image'].widget.attrs.pop('class', None)
        self.fields['profile_image'].widget = forms.ClearableFileInput(
            attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-3 bg-white'}
        )


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['title', 'company', 'start_year', 'end_year', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Type a message...',
                    'class': 'w-full rounded-xl border border-gray-200 p-3 focus:outline-none focus:ring-2 focus:ring-teal-500',
                }
            )
        }


class BrandedAuthenticationForm(AuthenticationForm):
    """Authentication form with placeholders to match the UI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = 'w-full mt-1 rounded-xl border border-slate-200 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500'
        self.fields['username'].widget.attrs.update({'placeholder': 'name@example.com', 'class': base_classes})
        self.fields['password'].widget.attrs.update({'placeholder': '••••••••', 'class': base_classes})

    def clean(self):
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
                self.cleaned_data['username'] = user.username
            except User.DoesNotExist:
                pass
        return super().clean()
