from django import forms
from .models import StockOut, StockOutDetail, Product

class StockOutForm(forms.ModelForm):
    class Meta:
        model = StockOut
        fields = ['notes', 'employee', 'customer', 'export_status', 'payment_status', 'amount_paid']
        widgets = {
            'notes': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Thêm ghi chú cho đơn hàng'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'export_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '0'}),
        }

class StockOutDetailForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = StockOutDetail
        fields = ['product', 'quantity', 'discount']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 100px;'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

StockOutDetailFormSet = forms.inlineformset_factory(
    StockOut, StockOutDetail, form=StockOutDetailForm, extra=1, can_delete=True
)