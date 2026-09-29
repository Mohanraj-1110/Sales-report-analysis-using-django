from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from accounts.models import CustomUser

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'Enter your username or email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': '••••••••'
    }))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'rounded border-slate-300 text-indigo-600 focus:ring-indigo-500'
    }))


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'name@company.com'
    }))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={
        'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition'
    }))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'placeholder': 'Choose a username'
        })
        self.fields['password_1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'placeholder': 'Create password'
        })
        self.fields['password_2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'placeholder': 'Confirm password'
        })


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100'}),
            'avatar': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }
