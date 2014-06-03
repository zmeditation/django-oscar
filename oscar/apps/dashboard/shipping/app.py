from django.conf.urls import url

from oscar.core.application import Application
from oscar.core.loading import get_class


class ShippingDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff']

    weight_method_list_view = get_class(
        'dashboard.shipping.views', 'WeightBasedListView')
    weight_method_create_view = get_class(
        'dashboard.shipping.views', 'WeightBasedCreateView')
    weight_method_edit_view = get_class(
        'dashboard.shipping.views', 'WeightBasedUpdateView')

    def get_urls(self):
        urlpatterns = [
            url(r'^weight-based/$', self.weight_method_list_view.as_view(),
                name='shipping-method-list'),
            url(r'^weight-based/create/$',
                self.weight_method_create_view.as_view(),
                name='shipping-method-create'),
            url(r'^weight-based/edit/(?P<pk>\d+)/$',
                self.weight_method_edit_view.as_view(),
                name='shipping-method-edit'),
        ]
        return self.post_process_urls(urlpatterns)


application = ShippingDashboardApplication()
