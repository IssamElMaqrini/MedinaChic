from django.contrib import admin

from store.models import Product, Order, Cart, OrderHistory, OrderHistoryItem, ProductReview, StockAlert

# Register your models here.
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Cart)


class OrderHistoryItemInline(admin.TabularInline):
    model = OrderHistoryItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'subtotal']


@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_date', 'total_amount']
    list_filter = ['order_date']
    search_fields = ['user__email']
    inlines = [OrderHistoryItemInline]
    readonly_fields = ['order_date']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'title', 'verified_purchase', 'created_at']
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Information du produit', {
            'fields': ('product', 'user', 'verified_purchase')
        }),
        ('Évaluation', {
            'fields': ('rating', 'title', 'comment')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'created_at', 'notified', 'notified_at']
    list_filter = ['notified', 'created_at', 'notified_at']
    search_fields = ['product__name', 'user__email']
    readonly_fields = ['created_at', 'notified_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Information', {
            'fields': ('product', 'user')
        }),
        ('État de la notification', {
            'fields': ('notified', 'created_at', 'notified_at')
        }),
    )