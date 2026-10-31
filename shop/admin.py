"""Админка: товары с инлайн-редактированием разновидностей и заказы."""
from django.contrib import admin

from .models import Category, Product, ProductVariant, Order


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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'contact_method',
                    'total_price', 'status', 'created_at')
    list_filter = ('status', 'contact_method', 'created_at')
    search_fields = ('customer_name', 'phone')
    readonly_fields = ('created_at', 'items_summary')
    fieldsets = (
        ('Клиент', {'fields': ('customer_name', 'phone', 'contact_method')}),
        ('Заказ', {'fields': ('items_summary', 'total_price', 'status')}),
        ('Мета', {'fields': ('created_at',)}),
    )
