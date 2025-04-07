from django.db import models


class ProductCategory(models.Model):
    category_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
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
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock = models.IntegerField()
    inspection_time = models.DateTimeField()
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=10)
    address = models.TextField()
    role = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class StockIn(models.Model):
    import_date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=50)
    import_status = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class StockOut(models.Model):
    export_date = models.DateTimeField()
    export_status = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class StockInDetail(models.Model):
    import_record = models.ForeignKey(StockIn, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    product_batch = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class StockOutDetail(models.Model):
    export_record = models.ForeignKey(StockOut, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
