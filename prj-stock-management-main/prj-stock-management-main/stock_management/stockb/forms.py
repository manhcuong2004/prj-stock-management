from django import forms
from .models import StockOut, StockOutDetail, Product, ProductCategory, InventoryCheck, InventoryCheckDetail, Unit, Supplier

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name', 'description', 'quantity', 'purchase_price',
            'selling_price', 'minimum_stock', 'inspection_time',
            'category', 'unit', 'supplier'
        ]
        labels = {
            'product_name': 'Tên sản phẩm',
            'description': 'Mô tả',
            'quantity': 'Số lượng',
            'purchase_price': 'Giá nhập vào',
            'selling_price': 'Giá bán ra',
            'minimum_stock': 'Số lượng tồn kho tối thiểu',
            'inspection_time': 'Thời gian kiểm tra',
            'category': 'Danh mục',
            'unit': 'Đơn vị',
            'supplier': 'Nhà cung cấp',
        }
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên sản phẩm'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Nhập mô tả sản phẩm', 'rows': 3}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
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
        labels = {
            'category_name': 'Tên danh mục',
            'description': 'Mô tả',
        }
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên danh mục'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập mô tả danh mục'}),
        }

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
    StockOut, StockOutDetail, form=StockOutDetailForm, extra=1, can_delete=True
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