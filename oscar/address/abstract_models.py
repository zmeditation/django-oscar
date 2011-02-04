"""
Core address objects
"""
import zlib

from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractAddress(models.Model):
    """
    Core address object
    
    This is normally subclassed and extended to provide models for 
    shipping and billing addresses.
    """
    # @todo: Need a way of making these choice lists configurable 
    # per project
    MR, MISS, MRS, MS, DR = ('Dr', 'Miss', 'Mrs', 'Ms', 'Dr')
    TITLE_CHOICES = (
        (MR, _("Mr")),
        (MISS, _("Miss")),
        (MRS, _("Mrs")),
        (MS, _("Ms")),
        (DR, _("Dr")),
    )
    # User is optional as this address could belong to an anonymous customer
    title = models.CharField(_("Title"), max_length=64, choices=TITLE_CHOICES, blank=True)
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255)
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    line3 = models.CharField(_("City"), max_length=255, blank=True)
    line4 = models.CharField(_("State/County"), max_length=255, blank=True)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64)
    # @todo: Create a country model to use as a foreign key
    country = models.CharField(_("Country"), max_length=255, blank=True)
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        # Ensure postcodes are always uppercase
        if self.postcode:
            self.postcode = self.postcode.upper()
        super(AbstractAddress, self).save(*args, **kwargs)    
        
    def summary(self):
        return ", ".join(self.active_address_fields())    
        
    def populate_alternative_model(self, address_model):
        ## Copy across all matching fields apart from id
        destination_field_names = list(address_model._meta.get_all_field_names())
        for field_name in self._meta.get_all_field_names():
            if field_name in destination_field_names and field_name != 'id':
                setattr(address_model, field_name, getattr(self, field_name))
                
        
    def active_address_fields(self):
        """
        Returns the non-empty components of the adddress, but merging the
        title, first_name and last_name into a single line.
        """
        return filter(lambda x: x, [self.salutation(), self.line1, self.line2, self.line3,
                                    self.line4, self.postcode, self.country])
        
    def salutation(self):
        """
        Returns the salutation
        """
        return " ".join([part for part in [self.title, self.first_name, self.last_name] if part])
        
    def __unicode__(self):
        parts = (self.salutation(), self.line1, self.line2, self.line3, self.line4,
                 self.postcode, self.country)
        return u", ".join([part for part in parts if part])


class AbstractShippingAddress(AbstractAddress):
    u"""
    Shipping address 
    """
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    notes = models.TextField(blank=True, null=True) 
    
    class Meta:
        abstract = True
        verbose_name_plural = "shipping addresses"
        
        
class AbstractUserAddress(AbstractShippingAddress):
    u"""
    A user address which forms an "AddressBook".
    
    We use a separate model to shipping and billing (even though there will be
    some data duplication) because we don't want shipping/billing addresses changed
    or deleted once an order has been placed.  By having a separate model, we allow
    users  
    """
    user = models.ForeignKey('auth.User', related_name='addresses')
    
    # We keep track of the number of times an address has been used
    # as a shipping address so we can show the most popular ones 
    # first at the checkout.
    num_orders = models.PositiveIntegerField(default=0)
    hash = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def generate_hash(self):
        # We use an uppercase version of the summary
        return zlib.crc32(self.summary().strip().upper())

    def save(self, *args, **kwargs):
        # Save a hash of the address fields so we can check whether two 
        # addresses are the same to avoid saving duplicates
        self.hash = self.generate_hash()
        super(AbstractUserAddress, self).save(*args, **kwargs)  
    
    class Meta:
        abstract = True
        verbose_name_plural = "User addresses"
        ordering = ['-num_orders']


class AbstractBillingAddress(AbstractAddress):
    """
    Billing address
    """
    class Meta:
        abstract = True
        verbose_name_plural = "Billing addresses"    
