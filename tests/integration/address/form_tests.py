from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.address import models, forms
from oscar.core.compat import get_user_model

User = get_user_model()


class TestUserAddressForm(TestCase):

    def setUp(self):
        self.user = G(User)
        self.country = models.Country.objects.create(
            iso_3166_1_a2='GB', name="UNITED KINGDOM")

    def test_merges_addresses_with_same_hash(self):
        data = {
            'user': self.user,
            'first_name': "Matus",
            'last_name': "Moravcik",
            'line1': "1 Egg Street",
            'line4': "London",
            'postcode': "N1 9RE",
            'country': self.country}

        # Create two addresses, which are slightly different
        models.UserAddress.objects.create(**data)
        other = data.copy()
        other['first_name'] = 'Izidor'
        duplicate = models.UserAddress.objects.create(**other)

        # Edit duplicate to be same as original and check that the two
        # addresses are merged when the form saves.
        post_data = data.copy()
        post_data['country'] = self.country.iso_3166_1_a2
        form = forms.UserAddressForm(self.user, post_data, instance=duplicate)
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors['__all__']) > 0)
