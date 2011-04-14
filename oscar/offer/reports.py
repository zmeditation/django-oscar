import csv

from oscar.services import import_module
report_classes = import_module('reports.reports', ['ReportGenerator'])
offer_models = import_module('offer.models', ['Voucher', 'ConditionalOffer'])


class VoucherReportGenerator(report_classes.ReportGenerator):
    
    filename_template = 'voucher-performance.csv'
    code = 'vouchers'
    description = 'Voucher performance'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['Voucher code',
                      'Added to a basket',
                      'Used in an order',
                      'Total discount',
                     ]
        writer.writerow(header_row)
        
        vouchers = offer_models.Voucher._default_manager.all()
        for voucher in vouchers:
            row = [voucher.code, voucher.num_basket_additions, voucher.num_orders, voucher.total_discount]
            writer.writerow(row)

    def filename(self):
        return self.filename_template
    
    
class OfferReportGenerator(report_classes.ReportGenerator):
    
    filename_template = 'conditional-offer-performance.csv'
    code = 'conditional-offers'
    description = 'Offer performance'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['Offer',
                      'Total discount',
                     ]
        writer.writerow(header_row)
        
        for offer in offer_models.ConditionalOffer._default_manager.all():
            row = [offer, offer.total_discount]
            writer.writerow(row)

    def filename(self):
        return self.filename_template