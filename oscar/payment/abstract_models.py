from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

class AbstractSource(models.Model):
    u"""
    A source of payment for an order.  
    
    This is normally a credit card which has been pre-authed
    for the order amount, but some applications will allow orders to be paid for using multiple
    sources such as cheque, credit accounts, gift cards.  Each payment source will have its own
    entry.
    """
    order = models.ForeignKey('order.Order', related_name='sources')
    type = models.ForeignKey('payment.SourceType')
    initial_amount = models.DecimalField(decimal_places=2, max_digits=12)
    balance = models.DecimalField(decimal_places=2, max_digits=12)
    reference = models.CharField(max_length=128, blank=True, null=True)
    
    class Meta:
        abstract = True

    def __unicode__(self):
        description = "Payment of %.2f from %s" % (self.initial_amount, self.type)
        if self.reference:
            description += " (reference: %s)" % self.reference
        return description
    
    
class AbstractSourceType(models.Model):
    u"""A type of payment source (eg Bankcard, Business account, Gift card)"""
    name = models.CharField(max_length=128)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class AbstractTransaction(models.Model):
    u"""
    A transaction for payment sources which need a secondary 'transaction' to actually take the money
    
    This applies mainly to credit card sources which can be a pre-auth for the money.  A 'complete'
    needs to be run later to debit the money from the account.
    """
    source = models.ForeignKey('payment.Source', related_name='transactions')
    type = models.CharField(max_length=128, blank=True)
    delta_amount = models.FloatField()
    reference = models.CharField(max_length=128)
    date_created = models.DateField()
    
    class Meta:
        abstract = True

    def __unicode__(self):
        return "Transaction of %.2f" % self.delta_amount


class AbstractBankcard(models.Model):
    user = models.ForeignKey('auth.User', related_name='bankcards')
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=32)
    expiry_date = models.DateField()
    
    # For payment partners who are storing the full card details for us
    partner_reference = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        self.number = self._get_obfuscated_number()
        super(AbstractBankcard, self).save(*args, **kwargs)    
        
    def _get_obfuscated_number(self):
        return "XXXX-XXXX-XXXX-%s" % self.number[-4:]
