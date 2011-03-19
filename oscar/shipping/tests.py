from decimal import Decimal as D

from django.utils import unittest
from django.test.client import Client

from oscar.shipping.methods import FreeShipping, FixedPriceShipping
from oscar.shipping.models import OrderAndItemLevelChargeMethod
from oscar.basket.models import Basket

class FreeShippingTest(unittest.TestCase):
    
    def test_shipping_is_free(self):
        method = FreeShipping()
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('0.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), method.basket_charge_excl_tax())
        
class FixedPriceShippingTest(unittest.TestCase):        
    
    def test_fixed_price_shipping_charges_for_empty_basket(self):
        method = FixedPriceShipping(D('10.00'), D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())
        
    def test_fixed_price_shipping_assumes_no_tax(self):
        method = FixedPriceShipping(D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())
        
class OrderAndItemLevelChargeMethodTest(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemLevelChargeMethod(price_per_order=D('5.00'), price_per_item=D('1.00'))
        self.basket = Basket()
        self.method.set_basket(self.basket)
    
    def test_order_level_charge_for_empty_basket(self):
        self.assertEquals(D('5.00'), self.method.basket_charge_incl_tax())
