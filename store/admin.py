from django.contrib import admin

from store.models import Product, Order, Cart, OrderHistory, OrderHistoryItem, ProductReview, StockAlert, ReturnRequest, ReturnRequestItem, Notification

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


class ReturnRequestItemInline(admin.TabularInline):
    model = ReturnRequestItem
    extra = 0
    readonly_fields = ['order_item', 'quantity']
    can_delete = False


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'user', 'status', 'get_items_count', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['order__id', 'user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'get_total_return_amount']
    date_hierarchy = 'created_at'
    inlines = [ReturnRequestItemInline]
    
    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Nombre d\'articles'
    
    fieldsets = (
        ('Information de la commande', {
            'fields': ('order', 'user')
        }),
        ('Détails du retour', {
            'fields': ('reason', 'photo', 'status', 'get_total_return_amount')
        }),
        ('Réponse administrateur', {
            'fields': ('admin_response',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Information de notification', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('État', {
            'fields': ('is_read',)
        }),
        ('Relation', {
            'fields': ('related_return_request',)
        }),
        ('Date', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )