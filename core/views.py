from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

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

def login_view(request):

    # If already logged in, send the user to the correct area
    if request.user.is_authenticated:

        # Admin
        if request.user.is_superuser:
            return redirect('admin_dashboard')

        # Staff
        try:
            request.user.staff_profile
            return redirect('staff_dashboard')

        except Staff.DoesNotExist:
            pass

        # Customer
        try:
            request.user.customer_profile
            return redirect('home')

        except Customer.DoesNotExist:
            return redirect('home')


    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )


        # ----------------------------------------------------
        # INVALID LOGIN
        # ----------------------------------------------------

        if user is None:

            messages.error(
                request,
                'Invalid username or password.'
            )

            return render(
                request,
                'login.html'
            )


        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if user.is_superuser:

            login(request, user)

            messages.success(
                request,
                'Welcome, Administrator!'
            )

            return redirect('admin_dashboard')


        # ----------------------------------------------------
        # STAFF
        # ----------------------------------------------------

        try:

            staff = user.staff_profile

            if not staff.is_active:

                messages.error(
                    request,
                    'This staff account is inactive.'
                )

                return render(
                    request,
                    'login.html'
                )

            login(request, user)

            messages.success(
                request,
                f'Welcome back, '
                f'{user.first_name or user.username}!'
            )

            return redirect('staff_dashboard')

        except Staff.DoesNotExist:
            pass


        # ----------------------------------------------------
        # CUSTOMER
        # ----------------------------------------------------

        try:

            user.customer_profile

            login(request, user)

            messages.success(
                request,
                f'Welcome back, '
                f'{user.first_name or user.username}!'
            )

            return redirect('home')

        except Customer.DoesNotExist:
            pass


        # ----------------------------------------------------
        # UNKNOWN ROLE
        # ----------------------------------------------------

        messages.error(
            request,
            'This account does not have a valid system role.'
        )


    return render(
        request,
        'login.html'
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

    today = timezone.localdate()

    selected_date = request.POST.get(
        'reservation_date',
        ''
    )

    selected_time = request.POST.get(
        'reservation_time',
        ''
    )

    selected_guests = request.POST.get(
        'number_of_guests',
        ''
    )

    selected_table_id = request.POST.get(
        'table',
        ''
    )

    special_request = request.POST.get(
        'special_request',
        ''
    )

    availability_message = None
    availability_type = None

    # --------------------------------------------------------
    # AVAILABLE TABLES
    # --------------------------------------------------------

    tables = RestaurantTable.objects.filter(
        is_available=True
    ).order_by(
        'table_number'
    )

    # If guests are selected, only show tables large enough
    if selected_guests:

        try:
            guests = int(selected_guests)

            tables = tables.filter(
                capacity__gte=guests
            )

        except (TypeError, ValueError):
            guests = None

    else:
        guests = None


    # --------------------------------------------------------
    # CHECK / BOOK
    # --------------------------------------------------------

    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        # ----------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------

        if not selected_date or not selected_time or not selected_guests or not selected_table_id:

            messages.error(
                request,
                'Please complete all required reservation fields.'
            )

            return render(
                request,
                'reservation.html',
                {
                    'today': today,
                    'tables': tables,
                    'selected_date': selected_date,
                    'selected_time': selected_time,
                    'selected_guests': selected_guests,
                    'selected_table_id': selected_table_id,
                    'special_request': special_request,
                }
            )


        # ----------------------------------------------------
        # VALIDATE GUEST NUMBER
        # ----------------------------------------------------

        try:
            guests = int(selected_guests)

        except (TypeError, ValueError):

            messages.error(
                request,
                'Invalid number of guests.'
            )

            return redirect('reservation')


        # ----------------------------------------------------
        # VALIDATE TABLE
        # ----------------------------------------------------

        table = get_object_or_404(
            RestaurantTable,
            id=selected_table_id
        )


        if not table.is_available:

            availability_message = (
                f'Table {table.table_number} is currently unavailable.'
            )

            availability_type = 'danger'

        elif table.capacity < guests:

            availability_message = (
                f'Table {table.table_number} can accommodate only '
                f'{table.capacity} people.'
            )

            availability_type = 'danger'

        else:

            # ------------------------------------------------
            # CHECK EXISTING RESERVATIONS
            # ------------------------------------------------

            conflicting_reservation = Reservation.objects.filter(
                table=table,
                reservation_date=selected_date,
                reservation_time=selected_time,
                status__in=['Pending', 'Confirmed']
            ).exists()


            if conflicting_reservation:

                availability_message = (
                    f'Table {table.table_number} is already reserved '
                    f'for {selected_date} at {selected_time}.'
                )

                availability_type = 'danger'

            else:

                availability_message = (
                    f'Table {table.table_number} is available '
                    f'for {guests} people.'
                )

                availability_type = 'success'


        # ----------------------------------------------------
        # CHECK AVAILABILITY ONLY
        # ----------------------------------------------------

        if action == 'check':

            return render(
                request,
                'reservation.html',
                {
                    'today': today,
                    'tables': tables,
                    'selected_date': selected_date,
                    'selected_time': selected_time,
                    'selected_guests': selected_guests,
                    'selected_table_id': selected_table_id,
                    'special_request': special_request,
                    'availability_message': availability_message,
                    'availability_type': availability_type,
                }
            )


        # ----------------------------------------------------
        # BOOK TABLE
        # ----------------------------------------------------

        if action == 'book':

            if availability_type != 'success':

                messages.error(
                    request,
                    availability_message
                )

                return render(
                    request,
                    'reservation.html',
                    {
                        'today': today,
                        'tables': tables,
                        'selected_date': selected_date,
                        'selected_time': selected_time,
                        'selected_guests': selected_guests,
                        'selected_table_id': selected_table_id,
                        'special_request': special_request,
                    }
                )


            try:

                customer = request.user.customer_profile

            except Customer.DoesNotExist:

                messages.error(
                    request,
                    'Customer profile not found.'
                )

                return redirect('reservation')


            # -----------------------------------------------
            # CREATE RESERVATION
            # -----------------------------------------------

            Reservation.objects.create(
                customer=customer,
                table=table,
                reservation_date=selected_date,
                reservation_time=selected_time,
                number_of_guests=guests,
                status='Pending',
                special_request=special_request,
            )


            messages.success(
                request,
                f'Reservation request submitted successfully for '
                f'Table {table.table_number}. '
                f'Your reservation is pending admin confirmation.'
            )

            return redirect('reservation')


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    return render(
        request,
        'reservation.html',
        {
            'today': today,
            'tables': tables,
            'selected_date': selected_date,
            'selected_time': selected_time,
            'selected_guests': selected_guests,
            'selected_table_id': selected_table_id,
            'special_request': special_request,
        }
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

        messages.error(
            request,
            "You do not have permission to perform this action."
        )

        return redirect('home')


    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )


    # ========================================================
    # CONFIRM RESERVATION
    # ========================================================

    if status == 'Confirmed':

        if reservation.status != 'Pending':

            messages.warning(
                request,
                'This reservation has already been processed.'
            )

            return redirect('admin_dashboard')


        table = reservation.table


        if table is None:

            messages.error(
                request,
                'This reservation does not have a table assigned.'
            )

            return redirect('admin_dashboard')


        if not table.is_available:

            messages.error(
                request,
                f'Table {table.table_number} is currently unavailable.'
            )

            return redirect('admin_dashboard')


        # Check whether another reservation already uses
        # this table at the same date and time.

        conflict = Reservation.objects.filter(
            table=table,
            reservation_date=reservation.reservation_date,
            reservation_time=reservation.reservation_time,
            status='Confirmed'
        ).exclude(
            id=reservation.id
        ).exists()


        if conflict:

            messages.error(
                request,
                f'Table {table.table_number} is already reserved '
                f'for that date and time.'
            )

            return redirect('admin_dashboard')


        reservation.status = 'Confirmed'
        reservation.save()


        table.is_available = False
        table.save()


        messages.success(
            request,
            f'Reservation for '
            f'{reservation.customer.user.get_full_name() or reservation.customer.user.username} '
            f'has been confirmed.'
        )


    # ========================================================
    # REJECT RESERVATION
    # ========================================================

    elif status == 'Cancelled':

        if reservation.status != 'Pending':

            messages.warning(
                request,
                'This reservation has already been processed.'
            )

            return redirect('admin_dashboard')


        reservation.status = 'Cancelled'
        reservation.save()


        messages.success(
            request,
            'Reservation has been rejected.'
        )


    return redirect('admin_dashboard')