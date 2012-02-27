from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.orders import views
from oscar.apps.dashboard.nav import register, Node

node = Node('Manage orders')
node.add_child(Node('Orders', 'dashboard:order-list'))
node.add_child(Node('Statistics', 'dashboard:order-summary'))
register(node)


class OrdersDashboardApplication(Application):
    name = None
    order_list_view = views.OrderListView
    order_detail_view = views.OrderDetailView
    shipping_address_view = views.ShippingAddressUpdateView
    line_detail_view = views.LineDetailView
    order_summary_view = views.OrderSummaryView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.order_list_view.as_view(), name='order-list'),
            url(r'^summary/$', self.order_summary_view.as_view(),
                name='order-summary'),
            url(r'^(?P<number>[-\w]+)/$',
                self.order_detail_view.as_view(), name='order-detail'),
            url(r'^(?P<number>[-\w]+)/notes/(?P<note_id>\d+)/$',
                self.order_detail_view.as_view(), name='order-detail-note'),
            url(r'^(?P<number>[-\w]+)/lines/(?P<line_id>\d+)/$',
                self.line_detail_view.as_view(), name='order-line-detail'),
            url(r'^(?P<number>[-\w]+)/shipping-address/$',
                self.shipping_address_view.as_view(), name='order-shipping-address'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = OrdersDashboardApplication()
