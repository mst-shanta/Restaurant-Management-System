from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from core.views import *



urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    # ========================================================
    # HOME
    # ========================================================

    path(
        '',
        home,
        name='home'
    ),

    # ========================================================
    # MENU
    # ========================================================

    path(
        'menu/',
        menu,
        name='menu'
    ),

    # ========================================================
    # CART
    # ========================================================

    path(
        'cart/',
        cart,
        name='cart'
    ),

    path(
        'cart/add/<int:item_id>/',
        add_to_cart,
        name='add_to_cart'
    ),

    path(
        'cart/update/<int:item_id>/',
        update_cart,
        name='update_cart'
    ),

    path(
        'cart/remove/<int:item_id>/',
        remove_from_cart,
        name='remove_from_cart'
    ),

    # ========================================================
    # CHECKOUT
    # ========================================================

    path(
        'checkout/',
        checkout,
        name='checkout'
    ),

    path(
        'order-success/<int:order_id>/',
        order_success,
        name='order_success'
    ),

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        'login/',
        login_view,
        name='login'
    ),

    path(
        'register/',
        register,
        name='register'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

    # ========================================================
    # RESERVATION
    # ========================================================

    path(
        'reservation/',
        reservation,
        name='reservation'
    ),

    # ========================================================
    # STAFF
    # ========================================================

    path(
        'staff/dashboard/',
        staff_dashboard,
        name='staff_dashboard'
    ),

    # ========================================================
    # ADMIN PANEL
    # ========================================================

    path(
        'admin-panel/dashboard/',
        admin_dashboard,
        name='admin_dashboard'
    ),
]


# ============================================================
# MEDIA
# ============================================================

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)