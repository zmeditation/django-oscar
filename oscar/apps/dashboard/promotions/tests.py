from django.core.urlresolvers import reverse

from oscar.test import ClientTestCase


class ViewTests(ClientTestCase):
    is_staff = True

    def test_pages_exist(self):
        urls = [reverse('dashboard:promotion-list'),
                reverse('dashboard:promotion-create-rawhtml')
               ]
        for url in urls:
            self.assertIsOk(self.client.get(url))

    def test_create_redirects(self):
        base_url = reverse('dashboard:promotion-create-redirect')
        types = ['rawhtml']
        for p_type in types:
            url = '%s?promotion_type=%s' % (base_url, p_type)
            self.assertIsRedirect(self.client.get(url))