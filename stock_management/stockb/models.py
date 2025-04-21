from django.db import models
from django.utils import timezone


class ProductCategory(models.Model):
    category_name = models.CharField(max_length=100)
    description = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Unit(models.Model):
    unit_name = models.CharField(max_length=50)
    unit_symbol = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Supplier(models.Model):
    supplier_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    tax_code = models.CharField(max_length=50)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock = models.IntegerField(default=0)
    inspection_time = models.DateTimeField()
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name




class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Nam'),
        ('F', 'Nữ'),
        ('O', 'Khác'),
    ]
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default=None
    )
    address = models.TextField()
    role = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True,null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class StockIn(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PAID', 'Đã thanh toán'),
        ('PARTIALLY_PAID', 'Còn nợ'),
    ]
    IMPORT_STATUS_CHOICES = [
        ('IN_PROGRESS', 'Đang xử lí'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    import_date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    import_status = models.CharField(
        max_length=20,
        choices=IMPORT_STATUS_CHOICES,
        default='IN_PROGRESS'
    )
    notes = models.TextField(blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class StockOut(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PARTIALLY_PAID', 'Còn nợ'),
        ('PAID', 'Đã thanh toán'),
    ]
    IMPORT_STATUS_CHOICES = [
        ('IN_PROGRESS', 'Đang xử lí'),
        ('COMPLETED', 'Đã hoàn thành'),
        ('CANCELLED', 'Đã hủy'),
    ]
    export_date = models.DateTimeField()
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    export_status = models.CharField(
        max_length=20,
        choices=IMPORT_STATUS_CHOICES,
        default='IN_PROGRESS'
    )
    notes = models.TextField(blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def total_amount(self):
        total = sum(
            detail.quantity * detail.product.selling_price * (1 - detail.discount / 100)
            for detail in self.stockoutdetail_set.all()
        )
        return total

    def remaining_debt(self):
        return self.total_amount() - self.amount_paid

    def __str__(self):
        return f"StockOut #{self.id} - {self.customer.first_name} {self.customer.last_name}"


class StockInDetail(models.Model):
    import_record = models.ForeignKey(StockIn, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    product_batch = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class StockOutDetail(models.Model):
    export_record = models.ForeignKey(StockOut, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_details')
    stock_in_detail = models.ForeignKey(StockInDetail, on_delete=models.CASCADE, related_name='product_details')
    product_batch = models.CharField(max_length=100)  # Tên lô hàng
    initial_quantity = models.IntegerField()  # Số lượng ban đầu
    remaining_quantity = models.IntegerField()
    import_date = models.DateTimeField()
    expiry_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'product_batch')

    def __str__(self):
        return f"{self.product.product_name} - Lô {self.product_batch}"

    def save(self, *args, **kwargs):
        if not self.initial_quantity:
            self.initial_quantity = self.stock_in_detail.quantity
        self.remaining_quantity = self.calculate_remaining_quantity()
        super().save(*args, **kwargs)

    def calculate_remaining_quantity(self):
        exported_quantity = sum(
            detail.quantity
            for detail in StockOutDetail.objects.filter(
                product=self.product,
                export_record__export_date__gte=self.import_date
            )
        )
        return max(0, self.initial_quantity - exported_quantity)



class InventoryCheck(models.Model):
    check_date = models.DateTimeField(default=timezone.now)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inventory Check #{self.id} - {self.check_date.strftime('%d/%m/%Y %H:%M')}"

class InventoryCheckDetail(models.Model):
    inventory_check = models.ForeignKey(InventoryCheck, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    product_batch = models.CharField(max_length=100, blank=True)  # Lô hàng (nếu có)
    theoretical_quantity = models.IntegerField()  # Số lượng lý thuyết
    actual_quantity = models.IntegerField()  # Số lượng thực tế
    discrepancy = models.IntegerField(editable=False)  # Chênh lệch
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('inventory_check', 'product', 'product_batch')

    def save(self, *args, **kwargs):
        # Tính toán số lượng lý thuyết dựa trên ProductDetail
        if not self.theoretical_quantity:
            product_details = ProductDetail.objects.filter(product=self.product, product_batch=self.product_batch)
            if product_details.exists():
                self.theoretical_quantity = product_details.first().remaining_quantity
            else:
                # Nếu không có ProductDetail, lấy từ Product.quantity
                self.theoretical_quantity = self.product.quantity

        # Tính chênh lệch
        self.discrepancy = self.actual_quantity - self.theoretical_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} (Batch: {self.product_batch or 'N/A'}) - Check #{self.inventory_check.id}"

