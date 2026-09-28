from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import *


# ============================================================
# HOME
# ============================================================

def home(request):
    return render(request, 'home.html')


# ============================================================
# MENU
# ============================================================

def menu(request):

    categories = Category.objects.prefetch_related(
        'menu_items'
    ).all()

    return render(
        request,
        'menu.html',
        {
            'categories': categories,
        }
    )


# ============================================================
# ADD TO CART
# ============================================================

def add_to_cart(request, item_id):

    if request.method != 'POST':
        return redirect('menu')

    item = get_object_or_404(
        MenuItem,
        id=item_id,
        available=True
    )

    cart = request.session.get('cart', {})

    item_id = str(item.id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    if item_id in cart:
        cart[item_id] += quantity
    else:
        cart[item_id] = quantity

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(
        request,
        f'{quantity} × {item.name} added to your cart.'
    )

    return redirect('menu')


# ============================================================
# CART
# ============================================================

def cart(request):

    cart_data = request.session.get('cart', {})

    cart_items = []
    total = 0

    for item_id, quantity in cart_data.items():

        try:
            item = MenuItem.objects.get(
                id=item_id,
                available=True
            )
        except MenuItem.DoesNotExist:
            continue

        subtotal = item.price * quantity
        total += subtotal

        cart_items.append({
            'item': item,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(
        request,
        'cart.html',
        {
            'cart_items': cart_items,
            'total': total,
        }
    )


# ============================================================
# UPDATE CART
# ============================================================

def update_cart(request, item_id):

    if request.method != 'POST':
        return redirect('cart')

    cart = request.session.get('cart', {})

    item_id = str(item_id)

    if item_id not in cart:
        return redirect('cart')

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        del cart[item_id]
    else:
        cart[item_id] = quantity

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


# ============================================================
# REMOVE FROM CART
# ============================================================

def remove_from_cart(request, item_id):

    if request.method != 'POST':
        return redirect('cart')

    cart = request.session.get('cart', {})

    item_id = str(item_id)

    if item_id in cart:
        del cart[item_id]

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.user.is_authenticated:
        return redirect('menu')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )

        if not username or not email or not password:
            messages.error(
                request,
                'Please fill in all required fields.'
            )
            return redirect('register')

        if password != confirm_password:
            messages.error(
                request,
                'Passwords do not match.'
            )
            return redirect('register')

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                'Username already exists.'
            )
            return redirect('register')

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                'Email is already registered.'
            )
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        Customer.objects.create(
            user=user,
            phone=phone,
            address=address,
        )

        login(request, user)

        messages.success(
            request,
            'Registration successful. Welcome!'
        )

        return redirect('menu')

    return render(request, 'register.html')


# ============================================================
# LOGIN
# ============================================================

# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    # --------------------------------------------------------
    # SELECTED ROLE FROM NAVBAR
    # --------------------------------------------------------

    selected_role = request.GET.get(
        'role',
        ''
    ).strip()


    # --------------------------------------------------------
    # ALREADY AUTHENTICATED
    # --------------------------------------------------------

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect('admin_dashboard')

        try:
            request.user.staff_profile
            return redirect('staff_dashboard')

        except Staff.DoesNotExist:
            pass

        try:
            request.user.customer_profile
            return redirect('home')

        except Customer.DoesNotExist:
            return redirect('home')


    # --------------------------------------------------------
    # LOGIN FORM
    # --------------------------------------------------------

    if request.method == 'POST':

        role = request.POST.get(
            'role',
            ''
        ).strip()

        username = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        # Keep the selected role if the form has an error
        selected_role = role


        # ----------------------------------------------------
        # CHECK ROLE SELECTION
        # ----------------------------------------------------

        if role not in [
            'customer',
            'staff',
            'admin'
        ]:

            messages.error(
                request,
                'Please select your login role.'
            )

            return render(
                request,
                'login.html',
                {
                    'selected_role': selected_role
                }
            )


        # ----------------------------------------------------
        # AUTHENTICATE USER
        # ----------------------------------------------------

        user = authenticate(
            request,
            username=username,
            password=password
        )


        if user is None:

            messages.error(
                request,
                'Invalid username or password.'
            )

            return render(
                request,
                'login.html',
                {
                    'selected_role': selected_role
                }
            )


        # ----------------------------------------------------
        # ADMIN LOGIN
        # ----------------------------------------------------

        if role == 'admin':

            if not user.is_superuser:

                messages.error(
                    request,
                    'This account is not an Administrator account.'
                )

                return render(
                    request,
                    'login.html',
                    {
                        'selected_role': selected_role
                    }
                )

            login(
                request,
                user
            )

            messages.success(
                request,
                'Welcome, Administrator!'
            )

            return redirect(
                'admin_dashboard'
            )


        # ----------------------------------------------------
        # STAFF LOGIN
        # ----------------------------------------------------

        if role == 'staff':

            try:

                staff = user.staff_profile

            except Staff.DoesNotExist:

                messages.error(
                    request,
                    'This account is not a Staff account.'
                )

                return render(
                    request,
                    'login.html',
                    {
                        'selected_role': selected_role
                    }
                )


            if not staff.is_active:

                messages.error(
                    request,
                    'This staff account is inactive.'
                )

                return render(
                    request,
                    'login.html',
                    {
                        'selected_role': selected_role
                    }
                )


            login(
                request,
                user
            )

            messages.success(
                request,
                f'Welcome back, '
                f'{user.first_name or user.username}!'
            )

            return redirect(
                'staff_dashboard'
            )


        # ----------------------------------------------------
        # CUSTOMER LOGIN
        # ----------------------------------------------------

        if role == 'customer':

            try:

                user.customer_profile

            except Customer.DoesNotExist:

                messages.error(
                    request,
                    'This account is not a Customer account.'
                )

                return render(
                    request,
                    'login.html',
                    {
                        'selected_role': selected_role
                    }
                )


            login(
                request,
                user
            )

            messages.success(
                request,
                f'Welcome back, '
                f'{user.first_name or user.username}!'
            )

            return redirect(
                'home'
            )


    # --------------------------------------------------------
    # GET REQUEST
    # --------------------------------------------------------

    return render(
        request,
        'login.html',
        {
            'selected_role': selected_role
        }
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out.'
    )

    return redirect('home')


# ============================================================
# CHECKOUT
# ============================================================

def checkout(request):

    if not request.user.is_authenticated:

        messages.info(
            request,
            'Please log in before proceeding to checkout.'
        )

        return redirect('login')

    cart_data = request.session.get('cart', {})

    if not cart_data:

        messages.warning(
            request,
            'Your cart is empty.'
        )

        return redirect('menu')

    checkout_items = []
    total = 0

    for item_id, quantity in cart_data.items():

        try:
            item = MenuItem.objects.get(
                id=item_id,
                available=True
            )
        except MenuItem.DoesNotExist:
            continue

        subtotal = item.price * quantity
        total += subtotal

        checkout_items.append({
            'item': item,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    if not checkout_items:

        messages.warning(
            request,
            'Your cart is empty.'
        )

        return redirect('menu')

    if request.method == 'POST':

        try:
            customer = request.user.customer_profile

        except Customer.DoesNotExist:

            messages.error(
                request,
                'Customer profile not found.'
            )

            return redirect('menu')

        with transaction.atomic():

            order = Order.objects.create(
                customer=customer,
                status='Pending',
                total_amount=total
            )

            for checkout_item in checkout_items:

                OrderItem.objects.create(
                    order=order,
                    menu_item=checkout_item['item'],
                    quantity=checkout_item['quantity'],
                    price_at_order=checkout_item['item'].price
                )

            Payment.objects.create(
                order=order,
                amount=total,
                payment_method='Cash',
                payment_status='Pending'
            )

        request.session['cart'] = {}
        request.session.modified = True

        return redirect(
            'order_success',
            order_id=order.id
        )

    return render(
        request,
        'checkout.html',
        {
            'checkout_items': checkout_items,
            'total': total,
        }
    )


# ============================================================
# ORDER SUCCESS
# ============================================================

def order_success(request, order_id):

    if not request.user.is_authenticated:
        return redirect('login')

    order = get_object_or_404(
        Order,
        id=order_id,
        customer__user=request.user
    )

    return render(
        request,
        'order_success.html',
        {
            'order': order,
        }
    )


# ============================================================
# RESERVATION
# ============================================================

@login_required
def reservation(request):

    from django.utils import timezone
    from datetime import datetime

    today = timezone.localdate()

    # Show currently available tables
    tables = RestaurantTable.objects.filter(
        is_available=True
    ).order_by(
        'table_number'
    )

    context = {
        'tables': tables,
        'today': today.strftime('%Y-%m-%d'),
    }

    if request.method == 'POST':

        reservation_date = request.POST.get(
            'reservation_date',
            ''
        )

        reservation_time = request.POST.get(
            'reservation_time',
            ''
        )

        number_of_guests = request.POST.get(
            'number_of_guests',
            ''
        )

        table_id = request.POST.get(
            'table',
            ''
        )

        special_request = request.POST.get(
            'special_request',
            ''
        ).strip()

        action = request.POST.get(
            'action',
            ''
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not all([
            reservation_date,
            reservation_time,
            number_of_guests,
            table_id
        ]):

            messages.error(
                request,
                'Please complete all required reservation fields.'
            )

            context.update({
                'selected_date': reservation_date,
                'selected_time': reservation_time,
                'selected_guests': number_of_guests,
                'selected_table_id': table_id,
                'special_request': special_request,
            })

            return render(
                request,
                'reservation.html',
                context
            )

        try:

            selected_date = datetime.strptime(
                reservation_date,
                '%Y-%m-%d'
            ).date()

            selected_time = datetime.strptime(
                reservation_time,
                '%H:%M'
            ).time()

            guests = int(number_of_guests)

        except (ValueError, TypeError):

            messages.error(
                request,
                'Invalid reservation information.'
            )

            return render(
                request,
                'reservation.html',
                context
            )

        # Date cannot be in the past
        if selected_date < today:

            messages.error(
                request,
                'Reservation date cannot be in the past.'
            )

            context.update({
                'selected_date': reservation_date,
                'selected_time': reservation_time,
                'selected_guests': number_of_guests,
                'selected_table_id': table_id,
                'special_request': special_request,
            })

            return render(
                request,
                'reservation.html',
                context
            )

        # Number of guests must be positive
        if guests < 1:

            messages.error(
                request,
                'Number of guests must be at least 1.'
            )

            return render(
                request,
                'reservation.html',
                context
            )

        # ----------------------------------------------------
        # FIND TABLE
        # ----------------------------------------------------

        try:

            selected_table = RestaurantTable.objects.get(
                id=table_id
            )

        except RestaurantTable.DoesNotExist:

            messages.error(
                request,
                'Selected table does not exist.'
            )

            return render(
                request,
                'reservation.html',
                context
            )

        # Check whether the table is currently available
        if not selected_table.is_available:

            messages.error(
                request,
                'This table is currently unavailable.'
            )

            return render(
                request,
                'reservation.html',
                context
            )

        # Check table capacity
        if selected_table.capacity < guests:

            messages.error(
                request,
                f'Table {selected_table.table_number} can only '
                f'accommodate {selected_table.capacity} people.'
            )

            context.update({
                'selected_date': reservation_date,
                'selected_time': reservation_time,
                'selected_guests': number_of_guests,
                'selected_table_id': table_id,
                'special_request': special_request,
            })

            return render(
                request,
                'reservation.html',
                context
            )

        # ----------------------------------------------------
        # CHECK EXISTING RESERVATION
        # ----------------------------------------------------

        existing_reservation = Reservation.objects.filter(
            table=selected_table,
            reservation_date=selected_date,
            reservation_time=selected_time,
            status__in=[
                'Pending',
                'Confirmed'
            ]
        ).exists()

        if existing_reservation:

            messages.error(
                request,
                'This table is already reserved for the selected '
                'date and time.'
            )

            context.update({
                'selected_date': reservation_date,
                'selected_time': reservation_time,
                'selected_guests': number_of_guests,
                'selected_table_id': table_id,
                'special_request': special_request,
            })

            return render(
                request,
                'reservation.html',
                context
            )

        # ----------------------------------------------------
        # CHECK AVAILABILITY
        # ----------------------------------------------------

        if action == 'check':

            messages.success(
                request,
                f'Table {selected_table.table_number} is available '
                f'for {guests} people on '
                f'{selected_date.strftime("%d %b %Y")} at '
                f'{selected_time.strftime("%I:%M %p")}.'
            )

            context.update({
                'selected_date': reservation_date,
                'selected_time': reservation_time,
                'selected_guests': number_of_guests,
                'selected_table_id': table_id,
                'special_request': special_request,
            })

            return render(
                request,
                'reservation.html',
                context
            )

        # ----------------------------------------------------
        # BOOK TABLE
        # ----------------------------------------------------

        if action == 'book':

            try:

                customer = request.user.customer_profile

            except Customer.DoesNotExist:

                messages.error(
                    request,
                    'Customer profile not found.'
                )

                return redirect('register')

            Reservation.objects.create(
                customer=customer,
                table=selected_table,
                reservation_date=selected_date,
                reservation_time=selected_time,
                number_of_guests=guests,
                status='Pending',
                special_request=special_request,
            )

            messages.success(
                request,
                'Your reservation request has been submitted. '
                'Please wait for admin confirmation.'
            )

            return redirect('reservation')

    return render(
        request,
        'reservation.html',
        context
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

def staff_dashboard(request):
    return render(
        request,
        'staff/dashboard.html'
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access the admin dashboard.")
        return redirect('home')

    from django.utils import timezone

    today = timezone.localdate()

    current_month_budget = Budget.objects.filter(
        month=today.month,
        year=today.year
    ).first()

    pending_reservations = Reservation.objects.filter(
        status='Pending'
    ).select_related(
        'customer',
        'table'
    ).order_by(
        'reservation_date',
        'reservation_time'
    )

    context = {
        'customer_count': Customer.objects.count(),
        'reservation_count': Reservation.objects.count(),
        'order_count': Order.objects.count(),

        'monthly_budget': (
            current_month_budget.amount
            if current_month_budget
            else 0
        ),

        'pending_reservations': pending_reservations,
    }

    return render(
        request,
        'admin_panel/dashboard.html',
        context
    )
@login_required
@require_POST
def update_reservation_status(request, reservation_id, status):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('home')

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    if status == 'Confirmed':

        # Find an available table that can accommodate the guests
        available_table = RestaurantTable.objects.filter(
            is_available=True,
            capacity__gte=reservation.number_of_guests
        ).order_by(
            'capacity'
        ).first()

        if not available_table:
            messages.error(
                request,
                "No available table can accommodate this reservation."
            )
            return redirect('admin_dashboard')

        reservation.table = available_table
        reservation.status = 'Confirmed'
        reservation.save()

        available_table.is_available = False
        available_table.save()

        messages.success(
            request,
            f"Reservation for {reservation.customer.user.get_full_name() or reservation.customer.user.username} has been confirmed."
        )

    elif status == 'Cancelled':

        # If the reservation already had a table, make it available again
        if reservation.table:
            reservation.table.is_available = True
            reservation.table.save()

        reservation.status = 'Cancelled'
        reservation.save()

        messages.success(
            request,
            "Reservation has been rejected."
        )

    return redirect('admin_dashboard')