from django.test import TestCase
from decimal import Decimal as D

from oscar.apps.partner import strategy
from oscar.apps.catalogue import models
from oscar.test import factories
from oscar.apps.basket.models import Line


class TestDefaultStrategy(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()

    def test_no_stockrecords(self):
        product = factories.create_product()
        info = self.strategy.fetch_for_product(product)
        self.assertFalse(info.availability.is_available_to_buy)
        self.assertIsNone(info.price.incl_tax)

    def test_one_stockrecord(self):
        product = factories.create_product(price=D('1.99'), num_in_stock=4)
        info = self.strategy.fetch_for_product(product)
        self.assertTrue(info.availability.is_available_to_buy)
        self.assertEqual(D('1.99'), info.price.excl_tax)
        self.assertEqual(D('1.99'), info.price.incl_tax)

    def test_product_which_doesnt_track_stock(self):
        product_class = models.ProductClass.objects.create(
            name="Digital", track_stock=False)
        product = factories.create_product(
            product_class=product_class,
            price=D('1.99'), num_in_stock=None)
        info = self.strategy.fetch_for_product(product)
        self.assertTrue(info.availability.is_available_to_buy)

    def test_line_method_is_same_as_product_one(self):
        product = factories.create_product()
        line = Line(product=product)
        info = self.strategy.fetch_for_line(line)
        self.assertFalse(info.availability.is_available_to_buy)
        self.assertIsNone(info.price.incl_tax)

    def test_free_product_is_available_to_buy(self):
        product = factories.create_product(price=D('0'), num_in_stock=1)
        info = self.strategy.fetch_for_product(product)
        self.assertTrue(info.availability.is_available_to_buy)
        self.assertTrue(info.price.exists)


class TestDefaultStrategyForParentProductWhoseVariantsHaveNoStockRecords(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()
        parent = factories.create_product()
        for x in range(3):
            factories.create_product(parent=parent)
        self.info = self.strategy.fetch_for_parent(parent)

    def test_specifies_product_is_unavailable(self):
        self.assertFalse(self.info.availability.is_available_to_buy)

    def test_specifies_correct_availability_code(self):
        self.assertEqual('unavailable', self.info.availability.code)

    def test_specifies_product_has_no_price(self):
        self.assertFalse(self.info.price.exists)


class TestDefaultStrategyForParentProductWithInStockVariant(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()
        parent = factories.create_product()
        factories.create_product(parent=parent, price=D('10.00'),
                                 num_in_stock=3)
        for x in range(2):
            factories.create_product(parent=parent)
        self.info = self.strategy.fetch_for_parent(parent)

    def test_specifies_product_is_available(self):
        self.assertTrue(self.info.availability.is_available_to_buy)

    def test_specifies_correct_availability_code(self):
        self.assertEqual('available', self.info.availability.code)

    def test_specifies_product_has_correct_price(self):
        self.assertEqual(D('10.00'), self.info.price.incl_tax)


class TestDefaultStrategyForParentProductWithOutOfStockVariant(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()
        parent = factories.create_product()
        factories.create_product(parent=parent, price=D('10.00'),
                                 num_in_stock=0)
        for x in range(2):
            factories.create_product(parent=parent)
        self.info = self.strategy.fetch_for_parent(parent)

    def test_specifies_product_is_unavailable(self):
        self.assertFalse(self.info.availability.is_available_to_buy)

    def test_specifies_correct_availability_code(self):
        self.assertEqual('unavailable', self.info.availability.code)

    def test_specifies_product_has_correct_price(self):
        self.assertEqual(D('10.00'), self.info.price.incl_tax)
