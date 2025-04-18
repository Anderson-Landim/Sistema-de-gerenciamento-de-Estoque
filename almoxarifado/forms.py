from django import forms
from .models import CustomUser, Item

from django.forms.widgets import ClearableFileInput


# Formulário para cadastro de almoxarife
class AlmoxarifeForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha"
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password", "categoria"]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# Formulário para cadastro de item
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['codigo', 'nome', 'descricao', 'quantidade']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# Lá em cima, reutilize o seu widget customizado:
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs.update({'multiple': True})
        super().__init__(attrs)

# Aqui está o formulário corrigido:
class MultiFotoForm(forms.Form):
    imagens = forms.ImageField(
        widget=MultiFileInput(),  # <- aqui é a mudança mais importante
        required=True
    )
