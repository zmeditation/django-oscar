class Base(object):
    #: Whether any prices exist
    exists = False

    #: Whether tax is known for this product (and session)
    is_tax_known = False

    # Normal price properties
    excl_tax = incl_tax = tax = None


class NoStockRecord(Base):
    """
    No stockrecord, therefore no prices
    """


class WrappedStockRecord(Base):

    def __init__(self, stockrecord):
        self.stockrecord = stockrecord

    @property
    def exists(self):
        return self.stockrecord is not None

    @property
    def excl_tax(self):
        return self.stockrecord.price_excl_tax

    @property
    def incl_tax(self):
        return self.stockrecord.price_incl_tax

    @property
    def tax(self):
        return self.stockrecord.price_tax
