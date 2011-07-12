from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from oscar.apps.partner.wrappers import get_partner_wrapper


class AbstractPartner(models.Model):
    u"""Fulfillment partner"""
    name = models.CharField(max_length=128, unique=True)
    
    # A partner can have users assigned to it.  These can be used
    # to provide authentication for webservices etc.
    users = models.ManyToManyField('auth.User', related_name="partners", blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Fulfillment partners'
        abstract = True
        permissions = (
            ("can_edit_stock_records", "Can edit stock records"),
            ("can_view_stock_records", "Can view stock records"),
            ("can_edit_product_range", "Can edit product range"),
            ("can_view_product_range", "Can view product range"),
            ("can_edit_order_lines", "Can edit order lines"),
            ("can_view_order_lines", "Can view order lines"),
        )
        
    def __unicode__(self):
        return self.name


class AbstractStockRecord(models.Model):
    u"""
    A basic stock record.
    
    This links a product to a partner, together with price and availability
    information.  Most projects will need to subclass this object to add custom
    fields such as lead_time, report_code, min_quantity.
    """
    product = models.OneToOneField('catalogue.Product', related_name="stockrecord")
    partner = models.ForeignKey('partner.Partner')
    partner_sku = models.CharField(_("Partner SKU"), max_length=128, blank=True)
    
    # Price info:
    # We deliberately don't store tax information to allow each project
    # to subclass this model and put its own fields for convey tax.
    price_currency = models.CharField(max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY)
    
    # This is the base price for calculations - tax should be applied 
    # by the appropriate method.  We don't store it here as its calculation is 
    # highly domain-specific.  It is NULLable because some items don't have a fixed
    # price.
    price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    
    # Retail price for this item
    price_retail = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    
    # Cost price is optional as not all partner supply it
    cost_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    
    # Stock level information
    num_in_stock = models.IntegerField(default=0, blank=True, null=True)
    num_allocated = models.IntegerField(default=0, blank=True, null=True)
    
    # Date information
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
    
    def decrement_num_in_stock(self, delta):
        """
        Decrement an item's stock level
        """
        if self.num_in_stock >= delta:
            self.num_in_stock -= delta
        self.num_allocated += delta
        self.save()
        
    def allocate(self, quantity):
        """
        Decrement an item's stock allocation.
        """
        self.num_allocated += quantity
        self.save()
        
    def set_discount_price(self, price):
        """
        A setter method for setting a new price.  
        
        This is called from within the "discount" app, which is responsible
        for applying fixed-discount offers to products.  We use a setter method
        so that this behaviour can be customised in projects.
        """
        self.price_excl_tax = price
        self.save()
        
    # Price retrieval methods - these default to no tax being applicable
    # These are intended to be overridden.   
    
    @property
    def is_available_to_buy(self):
        """
        Return whether this stockrecord allows the product to be purchased
        """
        return get_partner_wrapper(self.partner.name).is_available_to_buy(self)
    
    @property
    def availability(self):
        u"""Return an item's availability as a string"""
        return get_partner_wrapper(self.partner.name).availability(self)
    
    @property
    def dispatch_date(self):
        u"""
        Returns the estimated dispatch date for a line
        """
        return get_partner_wrapper(self.partner.name).dispatch_date(self)
    
    @property 
    def price_incl_tax(self):
        """
        Return a product's price including tax.
        
        This defaults to the price_excl_tax as tax calculations are 
        domain specific.  This class needs to be subclassed and tax logic
        added to this method.
        """
        return self.price_excl_tax + self.price_tax
    
    @property 
    def price_tax(self):
        u"""Return a product's tax value"""
        return 0
    
    def __unicode__(self):
        if self.partner_sku:
            return "%s (%s): %s" % (self.partner.name, self.partner_sku, self.product.title)
        else:
            return "%s: %s" % (self.partner.name, self.product.title)
