from django.contrib import admin

from store.models import Product, Order, Cart, OrderHistory, OrderHistoryItem

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