from django import forms
from .models import StockOut, StockOutDetail, Product, ProductDetail, InventoryCheck, InventoryCheckDetail

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
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control amount-paid', 'min': '0', 'value': '0'}),
        }

class StockOutDetailForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    product_detail = forms.ModelChoiceField(
        queryset=ProductDetail.objects.filter(remaining_quantity__gt=0),
        widget=forms.HiddenInput(),
        required=True
    )

    class Meta:
        model = StockOutDetail
        fields = ['product', 'quantity', 'discount', 'product_detail']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity', 'style': 'width: 100px;', 'min': '1'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control discount', 'min': '0', 'max': '100'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        product_detail = cleaned_data.get('product_detail')

        if product and quantity and product_detail:
            if product_detail.product != product:
                raise forms.ValidationError("Lô sản phẩm không thuộc sản phẩm đã chọn.")
            if quantity > product_detail.remaining_quantity:
                raise forms.ValidationError(
                    f"Lô {product_detail.product_batch} chỉ còn {product_detail.remaining_quantity} sản phẩm."
                )
        elif product and quantity and not product_detail:
            raise forms.ValidationError("Vui lòng chọn lô sản phẩm.")
        return cleaned_data
StockOutDetailFormSet = forms.inlineformset_factory(
    StockOut, StockOutDetail, form=StockOutDetailForm, extra=0, can_delete=True
)

from django import forms
from .models import StockIn, StockInDetail, Product, Supplier, User

class StockInForm(forms.ModelForm):
    product_batch = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Nhập mã lô'}),
        required=True
    )

    class Meta:
        model = StockIn
        fields = ['notes', 'employee', 'supplier', 'import_status', 'payment_status', 'product_batch']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control mb-2', 'placeholder': 'Thêm ghi chú cho đơn nhập kho'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'import_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_product_batch(self):
        product_batch = self.cleaned_data.get('product_batch')
        if not product_batch:
            raise forms.ValidationError("Mã lô không được để trống.")
        # Kiểm tra mã lô không trùng với các đơn nhập kho khác
        if StockIn.objects.filter(product_batch=product_batch).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"Mã lô {product_batch} đã được sử dụng.")
        return product_batch

class StockInDetailForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = StockInDetail
        fields = ['product', 'quantity', 'discount']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity', 'style': 'width: 100px;', 'min': '1'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control discount', 'min': '0', 'max': '100'}),
        }

StockInDetailFormSet = forms.inlineformset_factory(
    StockIn, StockInDetail, form=StockInDetailForm, extra=0, can_delete=True
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