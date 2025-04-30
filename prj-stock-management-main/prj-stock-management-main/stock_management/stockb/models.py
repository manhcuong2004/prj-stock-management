from django.db import models
from django.utils import timezone

class ProductCategory(models.Model):
    category_name = models.CharField(max_length=255, verbose_name="Tên danh mục")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    def __str__(self):
        return self.category_name  # Hiển thị tên danh mục trong dropdown list

    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Danh mục sản phẩm"

class Unit(models.Model):
    unit_name = models.CharField(max_length=50, verbose_name="Tên đơn vị")

    def __str__(self):
        return self.unit_name  # Hiển thị tên đơn vị trong dropdown list

    class Meta:
        verbose_name = "Đơn vị"
        verbose_name_plural = "Đơn vị"

class Supplier(models.Model):
    company_name = models.CharField(max_length=255, verbose_name="Tên công ty")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    def __str__(self):
        return self.company_name  # Hiển thị tên công ty trong dropdown list

    class Meta:
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"

class Product(models.Model):
    product_name = models.CharField(max_length=255, verbose_name="Tên sản phẩm")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    quantity = models.IntegerField(default=0, verbose_name="Số lượng")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá nhập vào")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá bán ra")
    minimum_stock = models.IntegerField(default=0, verbose_name="Số lượng tồn kho tối thiểu")
    inspection_time = models.DateTimeField(blank=True, null=True, verbose_name="Thời gian kiểm tra")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Ngày tạo")
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name="Danh mục")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="Đơn vị")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="Nhà cung cấp")

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"

class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_details')
    product_batch = models.CharField(max_length=50)
    remaining_quantity = models.IntegerField(default=0)
    import_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_name} - Lô {self.product_batch}"

class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class StockOut(models.Model):
    EXPORT_STATUS_CHOICES = [
        ('IN_PROGRESS', 'Đang xử lý'),
        ('COMPLETED', 'Hoàn thành'),
        ('CANCELLED', 'Hủy bỏ'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Đã thanh toán'),
        ('UNPAID', 'Chưa thanh toán'),
    ]

    export_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    export_status = models.CharField(max_length=20, choices=EXPORT_STATUS_CHOICES, default='IN_PROGRESS')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Xuất kho {self.id} - {self.customer}"

class StockOutDetail(models.Model):
    export_record = models.ForeignKey(StockOut, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.product_name} - Số lượng: {self.quantity}"

class StockIn(models.Model):
    import_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return f"Nhập kho {self.id} - {self.supplier}"

class StockInDetail(models.Model):
    import_record = models.ForeignKey(StockIn, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} - Số lượng: {self.quantity}"

class InventoryCheck(models.Model):
    check_date = models.DateTimeField(default=timezone.now)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Kiểm kê {self.id} - {self.check_date}"

class InventoryCheckDetail(models.Model):
    inventory_check = models.ForeignKey(InventoryCheck, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_batch = models.CharField(max_length=50)
    theoretical_quantity = models.IntegerField()
    actual_quantity = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_name} - Lô {self.product_batch}"