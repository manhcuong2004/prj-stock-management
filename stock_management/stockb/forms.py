from django import forms
from .models import StockOut, StockOutDetail, Product, ProductDetail, InventoryCheck, InventoryCheckDetail, Unit, \
    ProductCategory


class StockOutForm(forms.ModelForm):
    class Meta:
        model = StockOut
        fields = ['notes', 'employee', 'customer', 'payment_status', 'amount_paid']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control mb-2', 'placeholder': 'Thêm ghi chú cho đơn hàng'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
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
    class Meta:
        model = StockIn
        fields = ['notes', 'employee', 'supplier', 'payment_status', 'amount_paid']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control mb-2', 'placeholder': 'Thêm ghi chú cho đơn nhập kho'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control amount-paid', 'min': '0', 'value': '0'}),
        }

class StockInDetailForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    product_batch = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập mã lô'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            product_detail = ProductDetail.objects.filter(stock_in_detail=self.instance).first()
            if product_detail and product_detail.product_batch:
                self.fields['product_batch'].initial = product_detail.product_batch

    class Meta:
        model = StockInDetail
        fields = ['product', 'quantity', 'discount', 'product_batch']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity', 'style': 'width: 100px;', 'min': '1'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control discount', 'min': '0', 'max': '100'}),
        }

    def clean_product_batch(self):
        product_batch = self.cleaned_data.get('product_batch')
        product = self.cleaned_data.get('product')
        if not product_batch:
            raise forms.ValidationError("Mã lô không được để trống.")
        query = ProductDetail.objects.filter(product=product, product_batch=product_batch)
        if self.instance.pk:
            query = query.exclude(stock_in_detail=self.instance)
        if query.exists():
            raise forms.ValidationError(f"Mã lô {product_batch} đã được sử dụng cho sản phẩm này.")
        return product_batch

StockInDetailFormSet = forms.inlineformset_factory(
    StockIn, StockInDetail, form=StockInDetailForm, extra=0, can_delete=True
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
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.HiddenInput(),
        required=True
    )
    product_batch = forms.ModelChoiceField(
        queryset=ProductDetail.objects.all(),
        widget=forms.HiddenInput(),
        required=True
    )

    class Meta:
        model = InventoryCheckDetail
        fields = ['product', 'product_batch', 'theoretical_quantity', 'actual_quantity', 'notes']
        widgets = {
            'theoretical_quantity': forms.HiddenInput(),
            'actual_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_batch = cleaned_data.get('product_batch')
        actual_quantity = cleaned_data.get('actual_quantity')

        if product and product_batch:
            if product_batch.product != product:
                raise forms.ValidationError("Lô sản phẩm không thuộc sản phẩm đã chọn.")
            cleaned_data['theoretical_quantity'] = product_batch.remaining_quantity
        else:
            raise forms.ValidationError("Vui lòng chọn sản phẩm và lô sản phẩm.")

        if actual_quantity is None:
            raise forms.ValidationError("Số lượng thực tế không được để trống.")

        return cleaned_data

InventoryCheckDetailFormSet = forms.inlineformset_factory(
    InventoryCheck, InventoryCheckDetail, form=InventoryCheckDetailForm, extra=0, can_delete=True
)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name', 'description', 'purchase_price',
            'selling_price', 'minimum_stock', 'inspection_time',
            'category', 'unit', 'supplier'
        ]

        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên sản phẩm'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Nhập mô tả sản phẩm', 'rows': 3}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'inspection_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        empty_label="Chọn danh mục",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all(),
        empty_label="Chọn đơn vị",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        empty_label="Chọn nhà cung cấp",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['category_name', 'description']

        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên danh mục'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập mô tả danh mục'}),
        }