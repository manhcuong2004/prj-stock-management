from django import forms
from django.db.models import Sum
from .models import StockOut, StockOutDetail, Product, InventoryCheck, InventoryCheckDetail, ProductDetail, Unit

class StockOutForm(forms.ModelForm):
    class Meta:
        model = StockOut
        fields = ['notes', 'employee', 'customer', 'export_status', 'payment_status', 'amount_paid']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control mb-2', 'placeholder': 'Thêm ghi chú cho đơn hàng'}),
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
    StockOut, StockOutDetail, form=StockOutDetailForm, extra=0, can_delete=True
)


class InventoryCheckForm(forms.ModelForm):
    class Meta:
        model = InventoryCheck
        fields = ['check_date', 'employee', 'notes']
        widgets = {
            'check_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control mb-2', 'placeholder': 'Thêm ghi chú cho kiểm kê'}),
        }


class InventoryCheckDetailForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        if not product:
            raise forms.ValidationError("Vui lòng chọn sản phẩm trước khi nhập số lượng!")
        return cleaned_data

    def clean_actual_quantity(self):
        actual = self.cleaned_data['actual_quantity']
        if actual < 0:
            raise forms.ValidationError("Số lượng thực tế không thể âm!")

        # Kiểm tra nếu product đã được gán
        product = self.cleaned_data.get('product') or getattr(self.instance, 'product', None)
        if not product:
            return actual  # Trả về actual nếu chưa có product, sẽ được xử lý ở clean()

        theoretical = self.instance.theoretical_quantity or 0
        max_quantity = ProductDetail.objects.filter(product=product).aggregate(total=Sum('remaining_quantity'))[
                           'total'] or 0
        if actual > max_quantity:
            if not self.cleaned_data.get('notes', '').strip():
                raise forms.ValidationError("Vui lòng ghi chú lý do khi số lượng thực tế vượt quá lý thuyết!")
        return actual

    class Meta:
        model = InventoryCheckDetail
        fields = ['product', 'product_batch', 'theoretical_quantity', 'actual_quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'product_batch': forms.HiddenInput(),
            'theoretical_quantity': forms.HiddenInput(),
            'actual_quantity': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 100px;'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


InventoryCheckDetailFormSet = forms.inlineformset_factory(
    InventoryCheck, InventoryCheckDetail, form=InventoryCheckDetailForm, extra=1, can_delete=True
)


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['unit_name', 'unit_symbol']
        labels = {
            'unit_name': 'Tên đơn vị',
            'unit_symbol': 'Kí hiệu đơn vị',
        }
        widgets = {
            'unit_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nhập tên đơn vị', 'required': True}),
            'unit_symbol': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nhập kí hiệu đơn vị', 'required': True}),
        }