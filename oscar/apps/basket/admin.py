from django.contrib import admin
from django.db.models import get_model

Line = get_model('basket', 'line')


class LineInline(admin.TabularInline):
    model = Line
    readonly_fields = ('line_reference', 'product', 'price_excl_tax',
                       'price_incl_tax')


class LineAdmin(admin.ModelAdmin):
    list_display = ('id', 'basket', 'product', 'stockrecord', 'quantity',
                    'price_excl_tax', 'date_created')
    readonly_fields = ('basket', 'stockrecord', 'line_reference', 'product',
                       'price_excl_tax', 'price_incl_tax', 'quantity')


class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'status', 'num_lines', 'total_incl_tax',
                    'contains_a_voucher', 'date_created', 'date_submitted',
                    'time_before_submit')
    readonly_fields = ('owner', 'date_merged', 'date_submitted')
    inlines = [LineInline]


admin.site.register(get_model('basket', 'basket'), BasketAdmin)
admin.site.register(Line, LineAdmin)
admin.site.register(get_model('basket', 'LineAttribute'))
