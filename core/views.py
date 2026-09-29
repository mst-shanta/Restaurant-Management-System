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

# ============================================================
# STAFF DASHBOARD
# ============================================================

@login_required
def staff_dashboard(request):

    # Make sure the logged-in user is a staff member
    try:
        staff = request.user.staff_profile

    except Staff.DoesNotExist:

        messages.error(
            request,
            'Staff profile not found.'
        )

        return redirect('home')


    from django.utils import timezone

    today = timezone.localdate()


    # --------------------------------------------------------
    # CURRENT MONTH SALARY
    # --------------------------------------------------------

    current_salary = Salary.objects.filter(
        staff=staff,
        month=today.month,
        year=today.year
    ).first()


    # --------------------------------------------------------
    # LATEST PERFORMANCE
    # --------------------------------------------------------

    latest_performance = Performance.objects.filter(
        staff=staff
    ).order_by(
        '-evaluation_date'
    ).first()


    # --------------------------------------------------------
    # WORK SCHEDULE
    # --------------------------------------------------------

    schedules = Schedule.objects.filter(
        staff=staff,
        date__gte=today
    ).order_by(
        'date',
        'start_time'
    )


    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {
        'staff': staff,
        'current_salary': current_salary,
        'latest_performance': latest_performance,
        'schedules': schedules,
    }


    return render(
        request,
        'staff/dashboard.html',
        context
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

@login_required
def budget_management(request):
    if not request.user.is_superuser:
        messages.error(
            request,
            "You do not have permission to access budget management."
        )
        return redirect('home')

    from django.utils import timezone

    today = timezone.localdate()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            try:
                month = int(request.POST.get('month'))
                year = int(request.POST.get('year'))
                amount = request.POST.get('amount')
                description = request.POST.get('description', '').strip()

                if month < 1 or month > 12:
                    messages.error(request, "Please select a valid month.")
                    return redirect('budget_management')

                if year < 2000:
                    messages.error(request, "Please enter a valid year.")
                    return redirect('budget_management')

                if not amount:
                    messages.error(request, "Please enter a budget amount.")
                    return redirect('budget_management')

                if Budget.objects.filter(
                    month=month,
                    year=year
                ).exists():
                    messages.error(
                        request,
                        "A budget already exists for this month and year."
                    )
                    return redirect('budget_management')

                Budget.objects.create(
                    month=month,
                    year=year,
                    amount=amount,
                    description=description
                )

                messages.success(
                    request,
                    "Monthly budget added successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid budget information."
                )

            return redirect('budget_management')

        elif action == 'update':
            budget_id = request.POST.get('budget_id')

            budget = get_object_or_404(
                Budget,
                id=budget_id
            )

            try:
                month = int(request.POST.get('month'))
                year = int(request.POST.get('year'))
                amount = request.POST.get('amount')
                description = request.POST.get(
                    'description',
                    ''
                ).strip()

                if month < 1 or month > 12:
                    messages.error(request, "Please select a valid month.")
                    return redirect('budget_management')

                if year < 2000:
                    messages.error(request, "Please enter a valid year.")
                    return redirect('budget_management')

                if not amount:
                    messages.error(request, "Please enter a budget amount.")
                    return redirect('budget_management')

                duplicate = Budget.objects.filter(
                    month=month,
                    year=year
                ).exclude(id=budget.id).exists()

                if duplicate:
                    messages.error(
                        request,
                        "Another budget already exists for this month and year."
                    )
                    return redirect('budget_management')

                budget.month = month
                budget.year = year
                budget.amount = amount
                budget.description = description
                budget.save()

                messages.success(
                    request,
                    "Budget updated successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid budget information."
                )

            return redirect('budget_management')

        elif action == 'delete':
            budget_id = request.POST.get('budget_id')

            budget = get_object_or_404(
                Budget,
                id=budget_id
            )

            budget.delete()

            messages.success(
                request,
                "Budget deleted successfully."
            )

            return redirect('budget_management')

    budgets = Budget.objects.all().order_by('-year', '-month')

    month_names = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]

    context = {
        'budgets': budgets,
        'month_names': month_names,
        'current_month': today.month,
        'current_year': today.year,
    }

    return render(
        request,
        'admin_panel/budget.html',
        context
    )

# ============================================================
# MENU MANAGEMENT
# ============================================================

@login_required
def menu_management(request):
    if not request.user.is_superuser:
        messages.error(
            request,
            "You do not have permission to access menu management."
        )
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ========================================================
        # ADD MENU ITEM
        # ========================================================

        if action == 'add':
            category_id = request.POST.get('category')
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price')
            available = request.POST.get('available') == 'True'
            image = request.FILES.get('image')

            if not category_id or not name or not price:
                messages.error(
                    request,
                    "Category, name and price are required."
                )
                return redirect('menu_management')

            try:
                price = float(price)

                if price < 0:
                    messages.error(
                        request,
                        "Price cannot be negative."
                    )
                    return redirect('menu_management')

                category = get_object_or_404(
                    Category,
                    id=category_id
                )

                MenuItem.objects.create(
                    category=category,
                    name=name,
                    description=description,
                    price=price,
                    available=available,
                    image=image
                )

                messages.success(
                    request,
                    f"Menu item '{name}' added successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid menu item information."
                )

            return redirect('menu_management')

        # ========================================================
        # UPDATE MENU ITEM
        # ========================================================

        elif action == 'update':
            item_id = request.POST.get('item_id')

            item = get_object_or_404(
                MenuItem,
                id=item_id
            )

            category_id = request.POST.get('category')
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price')
            available = request.POST.get('available') == 'True'
            image = request.FILES.get('image')

            if not category_id or not name or not price:
                messages.error(
                    request,
                    "Category, name and price are required."
                )
                return redirect('menu_management')

            try:
                price = float(price)

                if price < 0:
                    messages.error(
                        request,
                        "Price cannot be negative."
                    )
                    return redirect('menu_management')

                category = get_object_or_404(
                    Category,
                    id=category_id
                )

                item.category = category
                item.name = name
                item.description = description
                item.price = price
                item.available = available

                if image:
                    item.image = image

                item.save()

                messages.success(
                    request,
                    f"Menu item '{name}' updated successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid menu item information."
                )

            return redirect('menu_management')

        # ========================================================
        # DELETE MENU ITEM
        # ========================================================

        elif action == 'delete':
            item_id = request.POST.get('item_id')

            item = get_object_or_404(
                MenuItem,
                id=item_id
            )

            item_name = item.name
            item.delete()

            messages.success(
                request,
                f"Menu item '{item_name}' deleted successfully."
            )

            return redirect('menu_management')

    # ============================================================
    # DATABASE DATA
    # ============================================================

    menu_items = MenuItem.objects.select_related(
        'category'
    ).order_by(
        'category__name',
        'name'
    )

    categories = Category.objects.all().order_by('name')

    context = {
        'menu_items': menu_items,
        'categories': categories,
    }

    return render(
        request,
        'admin_panel/menu.html',
        context
    )

@login_required
def table_management(request):
    if not request.user.is_superuser:
        messages.error(
            request,
            "You do not have permission to access table management."
        )
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ADD TABLE
        if action == 'add':
            try:
                table_number = int(request.POST.get('table_number'))
                capacity = int(request.POST.get('capacity'))

                if table_number < 1:
                    messages.error(
                        request,
                        "Table number must be greater than 0."
                    )
                    return redirect('table_management')

                if capacity < 1:
                    messages.error(
                        request,
                        "Table capacity must be at least 1."
                    )
                    return redirect('table_management')

                if RestaurantTable.objects.filter(
                    table_number=table_number
                ).exists():
                    messages.error(
                        request,
                        "A table with this number already exists."
                    )
                    return redirect('table_management')

                RestaurantTable.objects.create(
                    table_number=table_number,
                    capacity=capacity,
                    is_available=True
                )

                messages.success(
                    request,
                    f"Table {table_number} added successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid table information."
                )

            return redirect('table_management')

        # UPDATE TABLE
        elif action == 'update':
            table_id = request.POST.get('table_id')

            table = get_object_or_404(
                RestaurantTable,
                id=table_id
            )

            try:
                table_number = int(request.POST.get('table_number'))
                capacity = int(request.POST.get('capacity'))
                is_available = request.POST.get('is_available') == 'True'

                if table_number < 1:
                    messages.error(
                        request,
                        "Table number must be greater than 0."
                    )
                    return redirect('table_management')

                if capacity < 1:
                    messages.error(
                        request,
                        "Table capacity must be at least 1."
                    )
                    return redirect('table_management')

                duplicate = RestaurantTable.objects.filter(
                    table_number=table_number
                ).exclude(id=table.id).exists()

                if duplicate:
                    messages.error(
                        request,
                        "Another table already uses this table number."
                    )
                    return redirect('table_management')

                table.table_number = table_number
                table.capacity = capacity
                table.is_available = is_available
                table.save()

                messages.success(
                    request,
                    f"Table {table_number} updated successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid table information."
                )

            return redirect('table_management')

        # DELETE TABLE
        elif action == 'delete':
            table_id = request.POST.get('table_id')

            table = get_object_or_404(
                RestaurantTable,
                id=table_id
            )

            table_number = table.table_number
            table.delete()

            messages.success(
                request,
                f"Table {table_number} deleted successfully."
            )

            return redirect('table_management')

    tables = RestaurantTable.objects.all().order_by('table_number')

    context = {
        'tables': tables,
    }

    return render(
        request,
        'admin_panel/tables.html',
        context
    )

@login_required
def staff_management(request):
    if not request.user.is_superuser:
        messages.error(
            request,
            "You do not have permission to access staff management."
        )
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ========================================================
        # ADD STAFF
        # ========================================================

        if action == 'add':
            username = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            position = request.POST.get('position', '').strip()
            joining_date = request.POST.get('joining_date') or None
            password = request.POST.get('password', '').strip()

            if not username or not position or not password:
                messages.error(
                    request,
                    "Username, position and password are required."
                )
                return redirect('staff_management')

            if User.objects.filter(username=username).exists():
                messages.error(
                    request,
                    "A user with this username already exists."
                )
                return redirect('staff_management')

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                    )

                    Staff.objects.create(
                        user=user,
                        phone=phone,
                        position=position,
                        joining_date=joining_date,
                        is_active=True
                    )

                messages.success(
                    request,
                    f"Staff member {username} added successfully."
                )

            except Exception:
                messages.error(
                    request,
                    "Could not add the staff member."
                )

            return redirect('staff_management')


        # ========================================================
        # UPDATE STAFF
        # ========================================================

        elif action == 'update':
            staff_id = request.POST.get('staff_id')

            staff = get_object_or_404(
                Staff,
                id=staff_id
            )

            user = staff.user

            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            position = request.POST.get('position', '').strip()
            joining_date = request.POST.get('joining_date') or None
            is_active = request.POST.get('is_active') == 'True'
            password = request.POST.get('password', '').strip()

            if not position:
                messages.error(
                    request,
                    "Position is required."
                )
                return redirect('staff_management')

            user.first_name = first_name
            user.last_name = last_name

            if password:
                user.set_password(password)

            user.save()

            staff.phone = phone
            staff.position = position
            staff.joining_date = joining_date
            staff.is_active = is_active
            staff.save()

            messages.success(
                request,
                f"Staff member {user.username} updated successfully."
            )

            return redirect('staff_management')


        # ========================================================
        # DELETE STAFF
        # ========================================================

        elif action == 'delete':
            staff_id = request.POST.get('staff_id')

            staff = get_object_or_404(
                Staff,
                id=staff_id
            )

            username = staff.user.username

            staff.delete()

            messages.success(
                request,
                f"Staff member {username} deleted successfully."
            )

            return redirect('staff_management')


        # ========================================================
        # ADD SCHEDULE
        # ========================================================

        elif action == 'add_schedule':
            staff_id = request.POST.get('staff')
            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            status = request.POST.get(
                'status',
                'Scheduled'
            ).strip()

            if not staff_id or not date or not start_time or not end_time:
                messages.error(
                    request,
                    "Staff, date, start time and end time are required."
                )
                return redirect('staff_management')

            staff = get_object_or_404(
                Staff,
                id=staff_id
            )

            if start_time >= end_time:
                messages.error(
                    request,
                    "End time must be later than start time."
                )
                return redirect('staff_management')

            Schedule.objects.create(
                staff=staff,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status=status or 'Scheduled'
            )

            messages.success(
                request,
                "Staff schedule added successfully."
            )

            return redirect('staff_management')


        # ========================================================
        # UPDATE SCHEDULE
        # ========================================================

        elif action == 'update_schedule':
            schedule_id = request.POST.get('schedule_id')

            schedule = get_object_or_404(
                Schedule,
                id=schedule_id
            )

            staff_id = request.POST.get('staff')
            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            status = request.POST.get(
                'status',
                'Scheduled'
            ).strip()

            if not staff_id or not date or not start_time or not end_time:
                messages.error(
                    request,
                    "Staff, date, start time and end time are required."
                )
                return redirect('staff_management')

            staff = get_object_or_404(
                Staff,
                id=staff_id
            )

            if start_time >= end_time:
                messages.error(
                    request,
                    "End time must be later than start time."
                )
                return redirect('staff_management')

            schedule.staff = staff
            schedule.date = date
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.status = status or 'Scheduled'
            schedule.save()

            messages.success(
                request,
                "Staff schedule updated successfully."
            )

            return redirect('staff_management')


        # ========================================================
        # DELETE SCHEDULE
        # ========================================================

        elif action == 'delete_schedule':
            schedule_id = request.POST.get('schedule_id')

            schedule = get_object_or_404(
                Schedule,
                id=schedule_id
            )

            schedule.delete()

            messages.success(
                request,
                "Staff schedule deleted successfully."
            )

            return redirect('staff_management')


        # ========================================================
        # ADD SALARY
        # ========================================================

        elif action == 'add_salary':
            staff_id = request.POST.get('staff')
            month = request.POST.get('month')
            year = request.POST.get('year')
            amount = request.POST.get('amount')
            payment_date = request.POST.get('payment_date') or None
            is_paid = request.POST.get('is_paid') == 'True'

            if not staff_id or not month or not year or not amount:
                messages.error(
                    request,
                    "Staff, month, year and salary amount are required."
                )
                return redirect('staff_management')

            try:
                month = int(month)
                year = int(year)

                if month < 1 or month > 12:
                    messages.error(
                        request,
                        "Month must be between 1 and 12."
                    )
                    return redirect('staff_management')

                if year < 2000:
                    messages.error(
                        request,
                        "Please enter a valid year."
                    )
                    return redirect('staff_management')

                if float(amount) < 0:
                    messages.error(
                        request,
                        "Salary amount cannot be negative."
                    )
                    return redirect('staff_management')

                staff = get_object_or_404(
                    Staff,
                    id=staff_id
                )

                if Salary.objects.filter(
                    staff=staff,
                    month=month,
                    year=year
                ).exists():
                    messages.error(
                        request,
                        "A salary record already exists for this staff member for that month."
                    )
                    return redirect('staff_management')

                Salary.objects.create(
                    staff=staff,
                    month=month,
                    year=year,
                    amount=amount,
                    payment_date=payment_date,
                    is_paid=is_paid
                )

                messages.success(
                    request,
                    "Salary record added successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid salary information."
                )

            return redirect('staff_management')


        # ========================================================
        # UPDATE SALARY
        # ========================================================

        elif action == 'update_salary':
            salary_id = request.POST.get('salary_id')

            salary = get_object_or_404(
                Salary,
                id=salary_id
            )

            staff_id = request.POST.get('staff')
            month = request.POST.get('month')
            year = request.POST.get('year')
            amount = request.POST.get('amount')
            payment_date = request.POST.get('payment_date') or None
            is_paid = request.POST.get('is_paid') == 'True'

            try:
                month = int(month)
                year = int(year)

                if month < 1 or month > 12:
                    messages.error(
                        request,
                        "Month must be between 1 and 12."
                    )
                    return redirect('staff_management')

                if year < 2000:
                    messages.error(
                        request,
                        "Please enter a valid year."
                    )
                    return redirect('staff_management')

                if float(amount) < 0:
                    messages.error(
                        request,
                        "Salary amount cannot be negative."
                    )
                    return redirect('staff_management')

                staff = get_object_or_404(
                    Staff,
                    id=staff_id
                )

                duplicate = Salary.objects.filter(
                    staff=staff,
                    month=month,
                    year=year
                ).exclude(
                    id=salary.id
                ).exists()

                if duplicate:
                    messages.error(
                        request,
                        "Another salary record already exists for that staff member and month."
                    )
                    return redirect('staff_management')

                salary.staff = staff
                salary.month = month
                salary.year = year
                salary.amount = amount
                salary.payment_date = payment_date
                salary.is_paid = is_paid
                salary.save()

                messages.success(
                    request,
                    "Salary record updated successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter valid salary information."
                )

            return redirect('staff_management')


        # ========================================================
        # DELETE SALARY
        # ========================================================

        elif action == 'delete_salary':
            salary_id = request.POST.get('salary_id')

            salary = get_object_or_404(
                Salary,
                id=salary_id
            )

            salary.delete()

            messages.success(
                request,
                "Salary record deleted successfully."
            )

            return redirect('staff_management')


        # ========================================================
        # ADD PERFORMANCE / RATING
        # ========================================================

        elif action == 'add_performance':
            staff_id = request.POST.get('staff')
            evaluation_date = request.POST.get('evaluation_date')
            score = request.POST.get('score')
            comments = request.POST.get(
                'comments',
                ''
            ).strip()

            if not staff_id or not evaluation_date or not score:
                messages.error(
                    request,
                    "Staff, evaluation date and score are required."
                )
                return redirect('staff_management')

            try:
                score = float(score)

                if score < 0 or score > 100:
                    messages.error(
                        request,
                        "Performance score must be between 0 and 100."
                    )
                    return redirect('staff_management')

                staff = get_object_or_404(
                    Staff,
                    id=staff_id
                )

                Performance.objects.create(
                    staff=staff,
                    evaluation_date=evaluation_date,
                    score=score,
                    comments=comments
                )

                messages.success(
                    request,
                    "Performance rating added successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter a valid performance score."
                )

            return redirect('staff_management')


        # ========================================================
        # UPDATE PERFORMANCE / RATING
        # ========================================================

        elif action == 'update_performance':
            performance_id = request.POST.get('performance_id')

            performance = get_object_or_404(
                Performance,
                id=performance_id
            )

            staff_id = request.POST.get('staff')
            evaluation_date = request.POST.get('evaluation_date')
            score = request.POST.get('score')
            comments = request.POST.get(
                'comments',
                ''
            ).strip()

            try:
                score = float(score)

                if score < 0 or score > 100:
                    messages.error(
                        request,
                        "Performance score must be between 0 and 100."
                    )
                    return redirect('staff_management')

                staff = get_object_or_404(
                    Staff,
                    id=staff_id
                )

                performance.staff = staff
                performance.evaluation_date = evaluation_date
                performance.score = score
                performance.comments = comments
                performance.save()

                messages.success(
                    request,
                    "Performance rating updated successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter a valid performance score."
                )

            return redirect('staff_management')


        # ========================================================
        # DELETE PERFORMANCE
        # ========================================================

        elif action == 'delete_performance':
            performance_id = request.POST.get('performance_id')

            performance = get_object_or_404(
                Performance,
                id=performance_id
            )

            performance.delete()

            messages.success(
                request,
                "Performance rating deleted successfully."
            )

            return redirect('staff_management')


    # ============================================================
    # DATABASE DATA
    # ============================================================

    staff_members = Staff.objects.select_related(
        'user'
    ).order_by(
        'user__first_name',
        'user__last_name',
        'user__username'
    )

    schedules = Schedule.objects.select_related(
        'staff',
        'staff__user'
    ).order_by(
        '-date',
        'start_time'
    )

    salaries = Salary.objects.select_related(
        'staff',
        'staff__user'
    ).order_by(
        '-year',
        '-month',
        'staff__user__username'
    )

    performances = Performance.objects.select_related(
        'staff',
        'staff__user'
    ).order_by(
        '-evaluation_date'
    )

    context = {
        'staff_members': staff_members,
        'schedules': schedules,
        'salaries': salaries,
        'performances': performances,
    }

    return render(
        request,
        'admin_panel/staff.html',
        context
    )