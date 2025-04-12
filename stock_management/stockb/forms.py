from django import forms
from .models import Unit

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'symbol']
        labels = {
            'name': 'Tên đơn vị',
            'symbol': 'Kí hiệu đơn vị',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên đơn vị', 'required': True}),
            'symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập kí hiệu đơn vị', 'required': True}),
        }