"""Тесты магазина «Пряный кусок»."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Order, OrderItem, Product, ProductVariant


User = get_user_model()


class BaseSetUp(TestCase):
    """Общие фикстуры."""

    def setUp(self):
        self.category = Category.objects.create(name='Копчёности', slug='smoked')
        self.product = Product.objects.create(
            category=self.category,
            name='Грудинка на дубовых дровах',
            slug='grudinka',
            description='Коптится 14 часов на цельных дубовых дровах.',
            base_price=Decimal('890.00'),
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            title='Вес: 500 г',
            price=Decimal('890.00'),
            stock=10,
        )
        self.variant_kg = ProductVariant.objects.create(
            product=self.product,
            title='Вес: 1 кг',
            price=Decimal('1590.00'),
            stock=5,
        )

    def place_order(self, **overrides):
        data = {
            'variant_id': self.variant.pk,
            'name': 'Иван Иванов',
            'phone': '+79990000000',
            'contact_method': 'call',
            'quantity': '1',
        }
        data.update(overrides)
        return self.client.post(
            reverse('shop:place_order', kwargs={'slug': self.product.slug}),
            data,
        )


class CatalogTests(BaseSetUp):
    def test_index_renders_ok(self):
        response = self.client.get(reverse('shop:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Грудинка на дубовых дровах')

    def test_index_shows_only_active_products(self):
        Product.objects.create(
            category=self.category, name='Скрытый', slug='hidden',
            description='—', base_price=Decimal('100.00'), is_active=False,
        )
        response = self.client.get(reverse('shop:index'))
        self.assertNotContains(response, 'Скрытый')

    def test_product_detail_renders_ok(self):
        response = self.client.get(
            reverse('shop:product_detail', kwargs={'slug': 'grudinka'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вес: 500 г')
        self.assertContains(response, 'Вес: 1 кг')
        self.assertContains(response, '890')

    def test_inactive_product_returns_404(self):
        self.product.is_active = False
        self.product.save()
        response = self.client.get(
            reverse('shop:product_detail', kwargs={'slug': 'grudinka'})
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_slug_returns_404(self):
        response = self.client.get(
            reverse('shop:product_detail', kwargs={'slug': 'no-such-product'})
        )
        self.assertEqual(response.status_code, 404)


class OrderCreationTests(BaseSetUp):
    def test_order_with_quantity_one(self):
        response = self.place_order()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.customer_name, 'Иван Иванов')
        self.assertEqual(order.phone, '+79990000000')
        self.assertEqual(order.contact_method, 'call')
        self.assertEqual(order.total_price, Decimal('890.00'))
        self.assertIn('× 1', order.items_summary)

    def test_order_with_quantity_three_multiplies_price(self):
        self.place_order(quantity='3')
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_price, Decimal('2670.00'))
        self.assertIn('× 3', order.items_summary)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 7)

    def test_order_creates_order_item(self):
        self.place_order(quantity='2')
        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.variant, self.variant)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal('890.00'))
        self.assertEqual(item.subtotal, Decimal('1780.00'))

    def test_second_variant_price_used(self):
        self.place_order(variant_id=self.variant_kg.pk, quantity='2')
        order = Order.objects.first()
        self.assertEqual(order.total_price, Decimal('3180.00'))
        self.variant_kg.refresh_from_db()
        self.assertEqual(self.variant_kg.stock, 3)


class OrderValidationTests(BaseSetUp):
    def test_order_rejected_when_name_empty(self):
        self.place_order(name='')
        self.assertEqual(Order.objects.count(), 0)

    def test_order_rejected_when_phone_empty(self):
        self.place_order(phone='')
        self.assertEqual(Order.objects.count(), 0)

    def test_order_rejected_when_variant_missing(self):
        self.place_order(variant_id='')
        self.assertEqual(Order.objects.count(), 0)

    def test_order_rejected_when_quantity_exceeds_stock(self):
        self.place_order(quantity='999')
        self.assertEqual(Order.objects.count(), 0)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 10)

    def test_order_rejected_when_stock_zero(self):
        self.variant.stock = 0
        self.variant.save()
        self.place_order(quantity='1')
        self.assertEqual(Order.objects.count(), 0)

    def test_cannot_order_foreign_variant(self):
        other_product = Product.objects.create(
            category=self.category, name='Чужой', slug='other',
            description='—', base_price=Decimal('50.00'), is_active=True,
        )
        foreign_variant = ProductVariant.objects.create(
            product=other_product, title='1 кг',
            price=Decimal('50.00'), stock=10,
        )
        self.place_order(variant_id=foreign_variant.pk)
        self.assertEqual(Order.objects.count(), 0)
        foreign_variant.refresh_from_db()
        self.assertEqual(foreign_variant.stock, 10)

    def test_quantity_defaults_to_one_on_invalid_input(self):
        self.place_order(quantity='abc')
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_price, Decimal('890.00'))


class AdminTests(BaseSetUp):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.local', password='pass12345',
        )
        self.client.force_login(self.admin)

    def test_admin_products_list(self):
        response = self.client.get(reverse('admin:shop_product_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Грудинка')

    def test_admin_orders_list_with_item(self):
        self.place_order(quantity='2')
        response = self.client.get(reverse('admin:shop_order_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иван Иванов')

    def test_admin_order_detail_shows_inline_items(self):
        self.place_order(quantity='2')
        order = Order.objects.first()
        response = self.client.get(
            reverse('admin:shop_order_change', args=[order.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '890.00')
