"""
Модели магазина копчёностей.
Category -> Product -> ProductVariant; Order хранит позиции заказа.
"""
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Категория товаров (например: 'Горячее копчение', 'Деликатесы')."""

    name = models.CharField('Название', max_length=120)
    slug = models.SlugField('Слаг', max_length=120, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """Товар (например: 'Грудинка на дубовых дровах')."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория',
    )
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Слаг', max_length=200, unique=True)
    description = models.TextField(
        'Описание',
        help_text='Обязательно укажите, на каких дровах и сколько часов коптится продукт.',
    )
    image = models.ImageField('Изображение', upload_to='products/%Y/%m/', blank=True)
    base_price = models.DecimalField('Базовая цена, ₽', max_digits=10, decimal_places=2)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})


class ProductVariant(models.Model):
    """Разновидность: вес / формат / цельный кусок."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='Товар',
    )
    title = models.CharField('Название разновидности', max_length=120,
                             help_text='Например: "Вес: 500 г", "Цельный кусок"')
    price = models.DecimalField('Цена, ₽', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('Остаток на складе', default=0)

    class Meta:
        verbose_name = 'Разновидность'
        verbose_name_plural = 'Разновидности'
        ordering = ['price']

    def __str__(self):
        return f'{self.product.name} — {self.title}'


class Order(models.Model):
    """Заказ клиента. Сохраняем все поля на момент оформления (снапшот)."""

    CONTACT_CHOICES = [
        ('call', 'Звонок'),
        ('telegram', 'Telegram'),
    ]

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('done', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]

    # Данные клиента
    customer_name = models.CharField('Имя клиента', max_length=120)
    phone = models.CharField('Телефон', max_length=32)
    contact_method = models.CharField(
        'Способ связи', max_length=16, choices=CONTACT_CHOICES, default='call'
    )
    address = models.CharField(
        'Адрес доставки', max_length=500,
        help_text='Улица, дом, квартира, город',
    )

    # Сумма
    total_price = models.DecimalField('Итого, ₽', max_digits=10, decimal_places=2)

    # Статус и мета
    status = models.CharField(
        'Статус', max_length=16, choices=STATUS_CHOICES, default='new'
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    # Краткое текстовое описание состава заказа (для истории/уведомлений)
    items_summary = models.TextField(
        'Состав заказа', blank=True,
        help_text='Заполняется автоматически при оформлении.',
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.pk} — {self.customer_name} ({self.total_price} ₽)'

class OrderItem(models.Model):
    """Позиция заказа.

    Важно: поле `price` хранит цену на момент оформления заказа —
    это «снапшот» цены. Если владелец позже изменит цену товара,
    история заказов останется корректной (клиент увидит ту сумму,
    которую платил). Стандартная практика для интернет-магазинов."""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='Заказ',
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name='Товар',
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, verbose_name='Разновидность',
    )
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField(
        'Цена за единицу, ₽', max_digits=10, decimal_places=2,
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.name} — {self.variant.title} × {self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity
