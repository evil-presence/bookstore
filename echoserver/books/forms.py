from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, AuthenticationForm
from argon2 import PasswordHasher
from .models import CustomUser, Book

def argon2_hash(raw_password):
    ph = PasswordHasher(
        time_cost=2,
        memory_cost=102400,
        parallelism=8,
        hash_len=32,
        salt_len=16
    )
    return ph.hash(raw_password)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'email')

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True, label="Имя")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = argon2_hash(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = CustomUser

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = argon2_hash(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'price')