from decimal import Decimal as D

from django.utils import unittest
from django.test.client import Client
from django.contrib.auth.models import User

from oscar.apps.shipping.methods import Free, FixedPrice
from oscar.apps.shipping.models import OrderAndItemCharges, WeightBand, WeightBased
from oscar.apps.shipping.repository import Repository
from oscar.apps.shipping import Scales
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product
from oscar.test.decorators import dataProvider


class FreeTest(unittest.TestCase):

    def setUp(self):
        self.method = Free()
    
    def test_shipping_is_free_for_empty_basket(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), self.method.basket_charge_excl_tax())

    def test_shipping_is_free_for_nonempty_basket(self):
        basket = Basket()
        basket.add_product(create_product())
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), self.method.basket_charge_excl_tax())
        
        
class FixedPriceTest(unittest.TestCase):        
    
    def test_fixed_price_shipping_charges_for_empty_basket(self):
        method = FixedPrice(D('10.00'), D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())
        
    def test_fixed_price_shipping_assumes_no_tax(self):
        method = FixedPrice(D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())
        
    shipping_values = lambda: [('1.00',), 
                               ('5.00',), 
                               ('10.00',), 
                               ('12.00',)]    
        
    @dataProvider(shipping_values)    
    def test_different_values(self, value):
        method = FixedPrice(D(value))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D(value), method.basket_charge_excl_tax())
        
        
class OrderAndItemChargesTests(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('5.00'), price_per_item=D('1.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)
    
    def test_order_level_charge_for_empty_basket(self):
        self.assertEquals(D('5.00'), self.method.basket_charge_incl_tax())
        
    def test_single_item_basket(self):
        p = create_product()
        self.basket.add_product(p)
        self.assertEquals(D('5.00') + D('1.00'), self.method.basket_charge_incl_tax())
        
    def test_multi_item_basket(self):
        p = create_product()
        self.basket.add_product(p, 7)
        self.assertEquals(D('5.00') + 7*D('1.00'), self.method.basket_charge_incl_tax())


class ZeroFreeThresholdTest(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('10.00'), free_shipping_threshold=D('0.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)
    
    def test_free_shipping_with_empty_basket(self):
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        
    def test_free_shipping_with_nonempty_basket(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())


class NonZeroFreeThresholdTest(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('10.00'), free_shipping_threshold=D('20.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)
        
    def test_basket_below_threshold(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p)
        self.assertEquals(D('10.00'), self.method.basket_charge_incl_tax())
        
    def test_basket_on_threshold(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p, 4)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        
    def test_basket_above_threshold(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p, 8)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())


class ScalesTests(unittest.TestCase):

    def test_simple_weight_calculation(self):
        scales = Scales(attribute='weight')
        p = create_product(attributes={'weight': 1})
        self.assertEqual(1, scales.weigh_product(p))

    def test_default_weight_is_used_when_attribute_is_missing(self):
        scales = Scales(attribute='weight', default_weight=0.5)
        p = create_product()
        self.assertEqual(0.5, scales.weigh_product(p))

    def test_exception_is_raised_when_attribute_is_missing(self):
        scales = Scales(attribute='weight')
        p = create_product()
        with self.assertRaises(ValueError):
            scales.weigh_product(p)

    def test_weight_calculation_of_empty_basket(self):
        basket = Basket()

        scales = Scales(attribute='weight')
        self.assertEquals(0, scales.weigh_basket(basket))

    def test_weight_calculation_of_basket(self):
        basket = Basket()
        basket.add_product(create_product(attributes={'weight': 1}))
        basket.add_product(create_product(attributes={'weight': 2}))

        scales = Scales(attribute='weight')
        self.assertEquals(1+2, scales.weigh_basket(basket))


class WeightBasedMethodTests(unittest.TestCase):

    def setUp(self):
        self.standard = WeightBased.objects.create(name='Standard')
        self.express = WeightBased.objects.create(name='Express')

    def tearDown(self):
        self.standard.delete()
        self.express.delete()

    def test_get_band_for_lower_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(0.5)
        self.assertEqual(band.id, fetched_band.id)

    def test_get_band_for_higher_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(1.5)
        self.assertIsNone(fetched_band)

    def test_get_band_for_matching_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(1)
        self.assertEqual(band.id, fetched_band.id)

    def test_weight_to_is_upper_bound(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.assertEqual(1, band.weight_to)

    def test_weight_from_for_single_band(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.assertEqual(0, band.weight_from)

    def test_weight_from_for_multiple_bands(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        band = self.standard.objects.create(upper_limit=2, charge=D('8.00'))
        self.assertEqual(1, band.weight_from)

    def test_weight_from_for_multiple_bands(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        band = self.express.bands.create(upper_limit=2, charge=D('8.00'))
        self.assertEqual(0, band.weight_from)

    def test_get_band_for_series_of_bands(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.standard.bands.create(upper_limit=2, charge=D('8.00'))
        self.standard.bands.create(upper_limit=3, charge=D('12.00'))
        self.assertEqual(D('4.00'), self.standard.get_band_for_weight(0.5).charge)
        self.assertEqual(D('8.00'), self.standard.get_band_for_weight(1.5).charge)
        self.assertEqual(D('12.00'), self.standard.get_band_for_weight(2.5).charge)

    def test_get_band_for_series_of_bands_from_different_methods(self):
        self.express.bands.create(upper_limit=2, charge=D('8.00'))
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.standard.bands.create(upper_limit=3, charge=D('12.00'))
        self.assertEqual(D('12.00'), self.standard.get_band_for_weight(2.5).charge)


class RepositoryTests(unittest.TestCase):

    def setUp(self):
        self.repo = Repository()

    def test_default_method_is_free(self):
        user, basket = User(), Basket()
        methods = self.repo.get_shipping_methods(user, basket)
        self.assertEqual(1, len(methods))
        self.assertTrue(isinstance(methods[0], Free))

