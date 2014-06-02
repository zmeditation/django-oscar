# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django.db import models
from django.utils.translation import ugettext_lazy as _

from oscar.core import prices, loading
from oscar.models.fields import AutoSlugField

Scale = loading.get_class('shipping.scales', 'Scale')


class AbstractBase(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    code = AutoSlugField(_("Slug"), max_length=128, unique=True,
                         populate_from='name')
    name = models.CharField(_("Name"), max_length=128, unique=True)
    description = models.TextField(_("Description"), blank=True)

    # We allow shipping methods to be linked to a specific set of countries
    countries = models.ManyToManyField('address.Country', null=True,
                                       blank=True, verbose_name=_("Countries"))

    class Meta:
        abstract = True
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")
        ordering = ['name']

    def __unicode__(self):
        return self.name


class AbstractOrderAndItemCharges(AbstractBase):
    """
    Standard shipping method

    This method has two components:
    * a charge per order
    * a charge per item

    Many sites use shipping logic which fits into this system.  However, for
    more complex shipping logic, a custom shipping method object will need to
    be provided that subclasses ShippingMethod.
    """
    price_per_order = models.DecimalField(
        _("Price per order"), decimal_places=2, max_digits=12,
        default=D('0.00'))
    price_per_item = models.DecimalField(
        _("Price per item"), decimal_places=2, max_digits=12,
        default=D('0.00'))

    # If basket value is above this threshold, then shipping is free
    free_shipping_threshold = models.DecimalField(
        _("Free Shipping"), decimal_places=2, max_digits=12, blank=True,
        null=True)

    class Meta(AbstractBase.Meta):
        abstract = True
        verbose_name = _("Order and Item Charge")
        verbose_name_plural = _("Order and Item Charges")

    def calculate(self, basket):
        if (self.free_shipping_threshold is not None and
                basket.total_incl_tax >= self.free_shipping_threshold):
            return prices.Price(
                currency=basket.currency, excl_tax=D('0.00'),
                incl_tax=D('0.00'))

        charge = self.price_per_order
        for line in basket.lines.all():
            if line.product.is_shipping_required:
                charge += line.quantity * self.price_per_item

        # Zero tax is assumed...
        return prices.Price(
            currency=basket.currency,
            excl_tax=charge,
            incl_tax=charge)


class AbstractWeightBased(AbstractBase):
    upper_charge = models.DecimalField(
        _("Upper Charge"), decimal_places=2, max_digits=12, null=True,
        help_text=_("This is the charge when the weight of the basket "
                    "is greater than all the weight bands"""))

    # The attribute code to use to look up the weight of a product
    weight_attribute = 'weight'

    # The default weight to use (in Kg) when a product doesn't have a weight
    # attribute.
    default_weight = models.DecimalField(
        _("Default Weight"), decimal_places=3, max_digits=12,
        default=D('0.000'),
        help_text=_("Default product weight in Kg when no weight attribute "
                    "is defined"))

    class Meta(AbstractBase.Meta):
        abstract = True
        verbose_name = _("Weight-based Shipping Method")
        verbose_name_plural = _("Weight-based Shipping Methods")

    def calculate(self, basket):
        # Note, when weighing the basket, we don't check whether the item
        # requires shipping or not.  It is assumed that if something has a
        # weight, then it requires shipping.
        scale = Scale(attribute_code=self.weight_attribute,
                      default_weight=self.default_weight)
        weight = scale.weigh_basket(basket)
        band = self.get_band_for_weight(weight)
        if not band:
            if self.bands.all().exists() and self.upper_charge:
                charge = self.upper_charge
            else:
                charge = D('0.00')

        # Zero tax is assumed...
        return prices.Price(
            currency=basket.currency,
            excl_tax=charge,
            incl_tax=charge)

    def get_band_for_weight(self, weight):
        """
        Return the weight band for a given weight
        """
        bands = self.bands.filter(
            upper_limit__gte=weight).order_by('upper_limit')[:1]
        # Query return only one row, so we can evaluate it
        if not bands:
            # No band for this weight
            return None
        return bands[0]


class AbstractWeightBand(models.Model):
    """
    Represents a weight band which are used by the WeightBasedShipping method.
    """
    method = models.ForeignKey(
        'shipping.WeightBased', related_name='bands', verbose_name=_("Method"))
    upper_limit = models.DecimalField(
        _("Upper Limit"), decimal_places=3, max_digits=12,
        help_text=_("Enter upper limit of this weight band in kg. The lower "
                    "limit will be determined by the other weight bands."))
    charge = models.DecimalField(_("Charge"), decimal_places=2, max_digits=12)

    @property
    def weight_from(self):
        lower_bands = self.method.bands.filter(
            upper_limit__lt=self.upper_limit).order_by('-upper_limit')
        if not lower_bands:
            return D('0.000')
        return lower_bands[0].upper_limit

    @property
    def weight_to(self):
        return self.upper_limit

    class Meta:
        abstract = True
        ordering = ['method', 'upper_limit']
        verbose_name = _("Weight Band")
        verbose_name_plural = _("Weight Bands")

    def __unicode__(self):
        return _('Charge for weights up to %s kg') % (self.upper_limit,)
