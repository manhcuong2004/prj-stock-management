from django.db import models

# Model cho bảng Suppliers
class Supplier(models.Model):
    supplier_name = models.CharField(max_length=255)
    tax_code = models.CharField(max_length=50, unique=True)
    country = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    ward = models.CharField(max_length=100)
    address = models.TextField()
    landline_phone = models.CharField(max_length=20, blank=True, null=True)
    mobile_phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    manager_name = models.CharField(max_length=255, blank=True, null=True)
    supplier_notes = models.TextField(blank=True, null=True)
    supplier_status = models.BooleanField(default=True)  # True: Active, False: Inactive
    supplier_created_at = models.DateTimeField(auto_now_add=True)
    supplier_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.supplier_name

# Model cho bảng Units
class Unit(models.Model):
    unit_name = models.CharField(max_length=50, unique=True)
    unit_notes = models.TextField(blank=True, null=True)
    unit_status = models.BooleanField(default=True)  # True: Active, False: Inactive
    unit_created_at = models.DateTimeField(auto_now_add=True)
    unit_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.unit_name