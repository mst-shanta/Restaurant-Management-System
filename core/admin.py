from django.contrib import admin

from .models import (
    Customer,
    Category,
    MenuItem,
    RestaurantTable,
    Reservation,
    Order,
    OrderItem,
    Payment,
    Staff,
    Schedule,
    Salary,
    Performance,
    Budget,
)


# ============================================================
# CUSTOMER
# ============================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'phone',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'phone',
    )


# ============================================================
# CATEGORY
# ============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'description',
    )

    search_fields = ('name',)


# ============================================================
# MENU ITEM
# ============================================================

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'price',
        'available',
        'created_at',
    )

    list_filter = (
        'category',
        'available',
    )

    search_fields = (
        'name',
        'description',
    )


# ============================================================
# RESTAURANT TABLE
# ============================================================

@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'table_number',
        'capacity',
        'is_available',
    )

    list_filter = (
        'is_available',
        'capacity',
    )


# ============================================================
# RESERVATION
# ============================================================

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'table',
        'reservation_date',
        'reservation_time',
        'number_of_guests',
        'status',
    )

    list_filter = (
        'status',
        'reservation_date',
    )

    search_fields = (
        'customer__user__username',
        'customer__user__first_name',
        'customer__user__last_name',
    )


# ============================================================
# ORDER
# ============================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'order_date',
        'status',
        'total_amount',
    )

    list_filter = (
        'status',
        'order_date',
    )

    search_fields = (
        'customer__user__username',
        'customer__user__first_name',
        'customer__user__last_name',
    )


# ============================================================
# ORDER ITEM
# ============================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'menu_item',
        'quantity',
        'price_at_order',
        'subtotal',
    )

    search_fields = (
        'menu_item__name',
    )


# ============================================================
# PAYMENT
# ============================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'amount',
        'payment_method',
        'payment_status',
        'payment_date',
    )

    list_filter = (
        'payment_method',
        'payment_status',
    )


# ============================================================
# STAFF
# ============================================================

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'position',
        'phone',
        'joining_date',
        'is_active',
    )

    list_filter = (
        'position',
        'is_active',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'position',
    )


# ============================================================
# SCHEDULE
# ============================================================

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'staff',
        'date',
        'start_time',
        'end_time',
        'status',
    )

    list_filter = (
        'date',
        'status',
    )

    search_fields = (
        'staff__user__username',
        'staff__user__first_name',
        'staff__user__last_name',
    )


# ============================================================
# SALARY
# ============================================================

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'staff',
        'month',
        'year',
        'amount',
        'is_paid',
        'payment_date',
    )

    list_filter = (
        'year',
        'month',
        'is_paid',
    )

    search_fields = (
        'staff__user__username',
        'staff__user__first_name',
        'staff__user__last_name',
    )


# ============================================================
# PERFORMANCE
# ============================================================

@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'staff',
        'evaluation_date',
        'score',
    )

    list_filter = (
        'evaluation_date',
    )

    search_fields = (
        'staff__user__username',
        'staff__user__first_name',
        'staff__user__last_name',
    )


# ============================================================
# BUDGET
# ============================================================

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'month',
        'year',
        'amount',
        'description',
        'created_at',
    )

    list_filter = (
        'year',
        'month',
    )

    search_fields = (
        'description',
    )