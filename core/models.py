from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# ============================================================
# CUSTOMER
# ============================================================

class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# ============================================================
# MENU
# ============================================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    available = models.BooleanField(default=True)

    image = models.ImageField(
        upload_to='menu/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ============================================================
# RESTAURANT TABLE
# ============================================================

class RestaurantTable(models.Model):
    table_number = models.PositiveIntegerField(unique=True)

    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number}"


# ============================================================
# RESERVATION
# ============================================================

class Reservation(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    table = models.ForeignKey(
        RestaurantTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations'
    )

    reservation_date = models.DateField()
    reservation_time = models.TimeField()

    number_of_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    special_request = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.customer} - "
            f"{self.reservation_date} "
            f"{self.reservation_time}"
        )


# ============================================================
# ORDER
# ============================================================

class Order(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    order_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"Order #{self.id} - {self.customer}"


# ============================================================
# ORDER ITEM
# ============================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    price_at_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    @property
    def subtotal(self):
        return self.quantity * self.price_at_order

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"


# ============================================================
# PAYMENT
# ============================================================

class Payment(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile Banking', 'Mobile Banking'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default='Cash'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='Pending'
    )

    payment_date = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Payment for Order #{self.order.id}"


# ============================================================
# STAFF
# ============================================================

class Staff(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )

    phone = models.CharField(max_length=20, blank=True)

    position = models.CharField(max_length=100)

    joining_date = models.DateField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (
            self.user.get_full_name()
            or self.user.username
        )


# ============================================================
# STAFF SCHEDULE
# ============================================================

class Schedule(models.Model):

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='schedules'
    )

    date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(
        max_length=30,
        default='Scheduled'
    )

    def __str__(self):
        return (
            f"{self.staff} - "
            f"{self.date}"
        )


# ============================================================
# SALARY
# ============================================================

class Salary(models.Model):

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='salary_records'
    )

    month = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    year = models.PositiveIntegerField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    is_paid = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['staff', 'month', 'year'],
                name='unique_staff_salary_month'
            )
        ]

    def __str__(self):
        return (
            f"{self.staff} - "
            f"{self.month}/{self.year}"
        )


# ============================================================
# STAFF PERFORMANCE
# ============================================================

class Performance(models.Model):

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='performance_records'
    )

    evaluation_date = models.DateField()

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ]
    )

    comments = models.TextField(blank=True)

    def __str__(self):
        return (
            f"{self.staff} - "
            f"{self.evaluation_date}"
        )


# ============================================================
# MONTHLY BUDGET
# ============================================================

class Budget(models.Model):

    month = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    year = models.PositiveIntegerField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['month', 'year'],
                name='unique_budget_month'
            )
        ]

    def __str__(self):
        return f"Budget - {self.month}/{self.year}"