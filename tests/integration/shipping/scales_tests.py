from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.shipping import Scales
from oscar.apps.basket.models import Basket
from oscar.test import factories


class TestScales(TestCase):

    def test_weighs_uses_specified_attribute(self):
        scales = Scales(attribute_code='weight')
        p = factories.create_product(attributes={'weight': '1'})
        self.assertEqual(1, scales.weigh_product(p))

    def test_uses_default_weight_when_attribute_is_missing(self):
        scales = Scales(attribute_code='weight', default_weight=0.5)
        p = factories.create_product()
        self.assertEqual(0.5, scales.weigh_product(p))

    def test_raises_exception_when_attribute_is_missing(self):
        scales = Scales(attribute_code='weight')
        p = factories.create_product()
        with self.assertRaises(ValueError):
            scales.weigh_product(p)

    def test_returns_zero_for_empty_basket(self):
        basket = Basket()

        scales = Scales(attribute_code='weight')
        self.assertEquals(0, scales.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket(self):
        basket = factories.create_basket(empty=True)
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        info = factories.create_stockinfo(record)
        basket.add_product(
            factories.create_product(attributes={'weight': '1'}), info)
        basket.add_product(
            factories.create_product(attributes={'weight': '2'}), info)

        scales = Scales(attribute_code='weight')
        self.assertEquals(1+2, scales.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket_with_line_quantities(self):
        basket = factories.create_basket(empty=True)
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        info = factories.create_stockinfo(record)
        basket.add_product(factories.create_product(
            attributes={'weight': '1'}), info, quantity=3)
        basket.add_product(factories.create_product(
            attributes={'weight': '2'}), info, quantity=4)

        scales = Scales(attribute_code='weight')
        self.assertEquals(1*3+2*4, scales.weigh_basket(basket))
