from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import redirect_to

from oscar.core.loading import import_module
import_module('customer.views', ['OrderHistoryView', 'OrderDetailView', 'OrderLineView',
                                 'AddressBookView', 'AddressView', 'EmailHistoryView', 'EmailDetailView'], locals())

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', {'template_name': 'admin/login.html'}, name='oscar-customer-login'),
    url(r'^logout/$', 'logout', name='oscar-customer-logout'),
)

urlpatterns += patterns('oscar.apps.customer.views',
    url(r'^profile/$', 'profile', name='oscar-customer-profile'),
    url(r'^order-history/$', OrderHistoryView.as_view(), name='oscar-customer-order-history'),
    url(r'^order/(?P<order_number>[\w-]*)/$', login_required(OrderDetailView.as_view()), name='oscar-customer-order-view'),
    url(r'^order/(?P<order_number>[\w-]*)/line/(?P<line_id>\w+)$', login_required(OrderLineView.as_view()), name='oscar-customer-order-line'),
    url(r'^address-book/$', login_required(AddressBookView.as_view()), name='oscar-customer-address-book'),
    url(r'^address/(?P<address_id>\d+)/$', login_required(AddressView.as_view()), name='oscar-customer-address'),
    url(r'^email-history/$', login_required(EmailHistoryView.as_view()), name='oscar-customer-email-history'),
    url(r'^email/(?P<email_id>\d+)/$', login_required(EmailDetailView.as_view()), name='oscar-customer-email-view'),
    url(r'^$', redirect_to, {'url': 'profile/'})
)
