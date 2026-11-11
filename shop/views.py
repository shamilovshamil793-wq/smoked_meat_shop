"""Представления: главная, страница товара, оформление заказа."""
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Category, Order, OrderItem, Product, ProductVariant
from .vk_notify import send_order_to_vk


def index(request):
    """Главная: hero-блок, категории, активные товары."""
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).prefetch_related('variants')
    return render(request, 'shop/index.html', {
        'categories': categories,
        'products': products,
    })


def product_detail(request, slug):
    """Карточка товара с выбором разновидности."""
    product = get_object_or_404(
        Product.objects.prefetch_related('variants'),
        slug=slug,
        is_active=True,
    )
    return render(request, 'shop/product_detail.html', {'product': product})


@require_POST
def place_order(request, slug):
    """
    Оформление заказа.

    Логика по шагам:
    1. Валидация входных данных: имя, телефон, variant_id.
    2. Проверка, что variant_id принадлежит именно этому товару —
       защита от подмены через DevTools (клиент не может передать
       разновидность другого товара).
    3. Проверка остатка на складе (нельзя заказать больше, чем есть).
    4. Атомарное создание Order + OrderItem и списание со склада
       внутри одной транзакции — при любой ошибке всё откатится,
       остаток не уменьшится «в пустоту».
    5. Отправка уведомления в VK — ВНЕ транзакции, чтобы ошибка
       VK API не откатывала уже сохранённый заказ.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)

    variant_id = request.POST.get('variant_id')
    name = (request.POST.get('name') or '').strip()
    address = (request.POST.get('address') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    contact_method = request.POST.get('contact_method', 'call')

    errors = []
    variant = None

    if not name:
        errors.append('Укажите имя.')
    if not phone:
        errors.append('Укажите телефон.')
    if not address:
        errors.append('Укажите адрес доставки.')

    if variant_id:
	# Обязательно фильтруем по product=product: клиент может
        # подменить variant_id в DevTools и прислать разновидность
        # другого товара. Проверка гарантирует принадлежность.
        variant = ProductVariant.objects.filter(
            pk=variant_id, product=product
        ).first()
        if not variant:
            errors.append('Выбранная разновидность не найдена.')
    else:
        errors.append('Выберите разновидность товара.')

    if contact_method not in dict(Order.CONTACT_CHOICES):
        contact_method = 'call'

    if errors:
        for err in errors:
            messages.error(request, err)
        return redirect(product.get_absolute_url())

    # Количество: 1..99, по умолчанию 1
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, min(99, quantity))

    # Проверка наличия на складе
    if variant.stock < quantity:
        messages.error(
            request,
            f'На складе только {variant.stock} шт. «{variant.title}». '
            f'Уменьшите количество или выберите другой вес.'
        )
        return redirect(product.get_absolute_url())

    total = variant.price * quantity

    # Атомарно: создаём заказ, позицию заказа и списываем со склада
    with transaction.atomic():
        variant.stock -= quantity
        variant.save(update_fields=['stock'])

        order = Order.objects.create(
            customer_name=name,
            phone=phone,
            address=address,
            contact_method=contact_method,
            total_price=total,
            items_summary=(
                f'{product.name} — {variant.title} × {quantity} = {total} ₽'
            ),
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=quantity,
            price=variant.price,
        )

    # Уведомление в VK — вне транзакции: ошибка API не должна откатывать заказ
    send_order_to_vk(order)

    messages.success(
        request,
        'Спасибо! Заказ принят. Мы свяжемся с вами в ближайшее время.'
    )
    return redirect(reverse('shop:index'))
