from django import forms
from django.conf import settings
from django.forms.models import modelformset_factory, BaseModelFormSet
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model
from oscar.forms import widgets

Line = get_model('basket', 'line')
Basket = get_model('basket', 'basket')
Product = get_model('catalogue', 'product')


class BasketLineForm(forms.ModelForm):
    save_for_later = forms.BooleanField(
        initial=False, required=False, label=_('Save for Later'))

    def __init__(self, strategy, *args, **kwargs):
        super(BasketLineForm, self).__init__(*args, **kwargs)
        self.instance.strategy = strategy

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty > 0:
            self.check_max_allowed_quantity(qty)
            self.check_permission(qty)
        return qty

    def check_max_allowed_quantity(self, qty):
        is_allowed, reason = self.instance.basket.is_quantity_allowed(qty)
        if not is_allowed:
            raise forms.ValidationError(reason)

    def check_permission(self, qty):
        policy = self.instance.purchase_info.availability
        is_available, reason = policy.is_purchase_permitted(
            quantity=qty)
        if not is_available:
            raise forms.ValidationError(reason)

    class Meta:
        model = Line
        exclude = ('basket', 'product', 'stockrecord', 'line_reference',
                   'price_excl_tax', 'price_incl_tax', 'price_currency')


class BaseBasketLineFormSet(BaseModelFormSet):

    def __init__(self, strategy, *args, **kwargs):
        self.strategy = strategy
        super(BaseBasketLineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super(BaseBasketLineFormSet, self)._construct_form(
            i, strategy=self.strategy, **kwargs)

    def _should_delete_form(self, form):
        """
        Quantity of zero is treated as if the user checked the DELETE checkbox,
        which results in the basket line being deleted
        """
        if super(BaseBasketLineFormSet, self)._should_delete_form(form):
            return True
        if self.can_delete and 'quantity' in form.cleaned_data:
            return form.cleaned_data['quantity'] == 0


BasketLineFormSet = modelformset_factory(
    Line, form=BasketLineForm, formset=BaseBasketLineFormSet, extra=0,
    can_delete=True)


class SavedLineForm(forms.ModelForm):
    move_to_basket = forms.BooleanField(initial=False, required=False,
                                        label=_('Move to Basket'))

    class Meta:
        model = Line
        fields = ('id', 'move_to_basket')

    def __init__(self, strategy, basket, *args, **kwargs):
        self.strategy = strategy
        self.basket = basket
        super(SavedLineForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SavedLineForm, self).clean()
        if not cleaned_data['move_to_basket']:
            # skip further validation (see issue #666)
            return cleaned_data
        try:
            line = self.basket.lines.get(product=self.instance.product)
        except Line.DoesNotExist:
            desired_qty = self.instance.quantity
        else:
            desired_qty = self.instance.quantity + line.quantity

        result = self.strategy.fetch_for_product(self.instance.product)
        is_available, reason = result.availability.is_purchase_permitted(
            quantity=desired_qty)
        if not is_available:
            raise forms.ValidationError(reason)
        return cleaned_data


class BaseSavedLineFormSet(BaseModelFormSet):

    def __init__(self, strategy, basket, *args, **kwargs):
        self.strategy = strategy
        self.basket = basket
        super(BaseSavedLineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super(BaseSavedLineFormSet, self)._construct_form(
            i, strategy=self.strategy, basket=self.basket, **kwargs)


SavedLineFormSet = modelformset_factory(Line, form=SavedLineForm,
                                        formset=BaseSavedLineFormSet, extra=0,
                                        can_delete=True)


class BasketVoucherForm(forms.Form):
    code = forms.CharField(max_length=128, label=_('Code'))

    def __init__(self, *args, **kwargs):
        super(BasketVoucherForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()


class ProductSelectionForm(forms.Form):
    product_id = forms.IntegerField(min_value=1, label=_("Product ID"))

    def clean_product_id(self):
        id = self.cleaned_data['product_id']

        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            raise forms.ValidationError(
                _("This product is unavailable for purchase"))


class AddToBasketForm(forms.Form):
    # It looks a little weird having a product ID here but it's because the
    # product passed to the constructor is the *parent* when dealing with
    # variant products. This product ID is the actual product we want to add to
    # the basket (which can be different from the parent). We set
    # required=False as validation happens later on
    product_id = forms.IntegerField(widget=forms.HiddenInput(), required=False,
                                    min_value=1, label=_("Product ID"))
    quantity = forms.IntegerField(initial=1, min_value=1, label=_('Quantity'))

    def __init__(self, basket, product, purchase_info, *args, **kwargs):
        super(AddToBasketForm, self).__init__(*args, **kwargs)
        self.basket = basket
        self.product = product
        self.purchase_info = purchase_info
        if product:
            if product.is_group:
                self._create_group_product_fields(product)
            else:
                self._create_product_fields(product)

    # Dynamic form building method

    def _create_group_product_fields(self, product):
        """
        Adds the fields for a "group"-type product (eg, a parent product with a
        list of variants.

        Currently requires that a stock record exists for the variant
        """
        choices = []
        disabled_values = []
        for variant in product.variants.all():
            attr_summary = variant.attribute_summary
            if attr_summary:
                summary = attr_summary
            else:
                summary = variant.get_title()
            info = self.request.strategy.fetch_for_product(variant)
            if not info.availability.is_available_to_buy:
                disabled_values.append(variant.id)
            choices.append((variant.id, summary))

        self.fields['product_id'] = forms.ChoiceField(
            choices=tuple(choices), label=_("Variant"),
            widget=widgets.AdvancedSelect(disabled_values=disabled_values))

    def _create_product_fields(self, product):
        """
        Add the product option fields.
        """
        for option in product.options:
            self._add_option_field(product, option)

    def _add_option_field(self, product, option):
        """
        Creates the appropriate form field for the product option.

        This is designed to be overridden so that specific widgets can be used
        for certain types of options.
        """
        kwargs = {'required': option.is_required}
        self.fields[option.code] = forms.CharField(**kwargs)

    # Cleaning

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.basket.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                raise forms.ValidationError(
                    _("Due to technical limitations we are not able to ship"
                      " more than %(threshold)d items in one order. Your"
                      " basket currently has %(basket)d items.")
                    % {'threshold': basket_threshold,
                       'basket': total_basket_quantity})
        return qty

    def clean(self):
        # Check product exists - we do this here rather than in a
        # clean_product_id method as the product ID is normally hidden and
        # so the error message won't be visible. Checking here means the error
        # message is treated as a "non-field error".
        try:
            product = Product.objects.get(
                id=self.cleaned_data.get('product_id', None))
        except Product.DoesNotExist:
            raise forms.ValidationError(
                _("Please select a valid product"))

        # Check user has permission to add the desired quantity to their
        # basket.
        current_qty = self.basket.product_quantity(product)
        desired_qty = current_qty + self.cleaned_data.get('quantity', 1)
        is_permitted, reason = self.purchase_info.availability.is_purchase_permitted(
            desired_qty)
        if not is_permitted:
            raise forms.ValidationError(reason)

        return self.cleaned_data

    # Helpers

    def cleaned_options(self):
        """
        Return submitted options in a clean format
        """
        options = []
        for option in self.product.options:
            if option.code in self.cleaned_data:
                options.append({
                    'option': option,
                    'value': self.cleaned_data[option.code]})
        return options


class SimpleAddToBasketForm(AddToBasketForm):
    """
    Simpified version of the add to basket form where the quantity is defaulted
    to 1 and rendered in a hidden widget
    """
    quantity = forms.IntegerField(
        initial=1, min_value=1, widget=forms.HiddenInput, label=_('Quantity'))
