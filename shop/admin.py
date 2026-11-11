"""Админка: товары с inline-разновидностями, заказы с inline-позициями."""
from django.contrib import admin

from .models import Category, Order, OrderItem, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class ProductVariantInline(admin.TabularInline):
    """Разновидности (вес/цена/остаток) редактируются прямо в карточке товара."""
    model = ProductVariant
    extra = 1
    fields = ('title', 'price', 'stock')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]


class OrderItemInline(admin.TabularInline):
    """Позиции заказа видны прямо в карточке заказа."""
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone','address', 'contact_method',
                    'total_price', 'status', 'created_at')
    list_filter = ('status', 'contact_method', 'created_at')
    search_fields = ('customer_name', 'phone')
    readonly_fields = ('created_at', 'items_summary')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Клиент', {'fields': ('customer_name', 'phone','address', 'contact_method')}),
        ('Заказ', {'fields': ('items_summary', 'total_price', 'status')}),
        ('Мета', {'fields': ('created_at',)}),
    )
