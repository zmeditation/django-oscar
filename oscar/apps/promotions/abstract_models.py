from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from oscar.forms.fields import ExtendedURLField

# Settings-controlled stuff
BANNER_FOLDER = settings.OSCAR_BANNER_FOLDER
POD_FOLDER = settings.OSCAR_POD_FOLDER
BLOCK_TYPES = settings.OSCAR_PROMOTION_MERCHANDISING_BLOCK_TYPES

BANNER, LEFT_POD, RIGHT_POD, RAW_HTML = ('Banner', 'Left pod', 'Right pod', 'Raw HTML')
POSITION_CHOICES = (
    (BANNER, _("Banner")),
    (LEFT_POD, _("Pod on left-hand side of page")),
    (RIGHT_POD, _("Pod on right-hand side of page")),
)


class AbstractPromotion(models.Model):
    """
    A promotion model.

    This is effectively a link for directing users to different parts of the site.
    It can have two images associated with it.

    """
    name = models.CharField(_("Name"), max_length=128)
    link_url = ExtendedURLField(blank=True, null=True, help_text="""This is 
        where this promotion links to""")

    banner_image = models.ImageField(upload_to=BANNER_FOLDER, blank=True, null=True)
    pod_image = models.ImageField(upload_to=POD_FOLDER, blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)

    _proxy_link_url = None
    
    image_html_template = '<img src="%s" alt="%s" />'
    link_html = '<a href="%s">%s</a>'

    class Meta:
        abstract = True
        ordering = ['date_created']
        get_latest_by = "date_created"
        
    def __unicode__(self):
        if not self.link_url:
            return self.name
        return "%s (%s)" % (self.name, self.link_url)   
        
    def clean(self):
        if not self.banner_image and not self.pod_image:
            raise ValidationError("A promotion must have one of a banner image, pod image or raw HTML")    
        
    def set_proxy_link(self, url):
        self._proxy_link_url = url    
        
    @property    
    def has_link(self):
        return self.link_url != None    

    def get_banner_html(self):
        return self._get_html('banner_image')

    def get_pod_html(self):
        return self._get_html('pod_image')

    def _get_html(self, image_field):
        u"""
        Returns the appropriate HTML for an image field
        """
        try:
            image = getattr(self, image_field)
            image_html = self.image_html_template % (image.url, self.name)
            if self.link_url and self._proxy_link_url:
                return self.link_html % (self._proxy_link_url, image_html)
            return image_html
        except AttributeError:
            return ''


class LinkedPromotion(models.Model):

    promotion = models.ForeignKey('promotions.Promotion')
    position = models.CharField(_("Position"), max_length=100, help_text="Position on page", choices=POSITION_CHOICES)
    display_order = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-clicks']

    def record_click(self):
        self.clicks += 1
        self.save()


class AbstractPagePromotion(LinkedPromotion):
    u"""
    A promotion embedded on a particular page.
    """
    page_url = ExtendedURLField(max_length=128, db_index=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"%s on %s" % (self.promotion, self.page_url)
    
    def get_link(self):
        return reverse('promotions:page-click', kwargs={'page_promotion_id': self.id})
        
    
class AbstractKeywordPromotion(LinkedPromotion):
    u"""
    A promotion linked to a specific keyword.

    This can be used on a search results page to show promotions
    linked to a particular keyword.
    """

    keyword = models.CharField(_("Keyword"), max_length=200)

    class Meta:
        abstract = True

    def get_link(self):
        return reverse('promotions:keyword-click', kwargs={'keyword_promotion_id': self.id})
    
    
class AbstractMerchandisingBlock(models.Model):
    
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(_("Type"), choices=BLOCK_TYPES, max_length=100)
    products = models.ManyToManyField('product.Item', through='MerchandisingBlockProduct', blank=True, null=True)
    link_url = ExtendedURLField(max_length=128, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.title    
        
    def template_context(self, *args, **kwargs):
        """
        Returns dynamically generated HTML that isn't product related.
        
        This can be used for novel forms of block.
        """
        method = 'template_context_%s' % self.type.lower()
        if hasattr(self, method):
            return getattr(self, method)(*args, **kwargs)
        return {}
    
    def template_context_tabbedblock(self, *args, **kwargs):
        # Split into groups
        groups = {}
        match = 0
        counter = 0
        for blockproduct in MerchandisingBlockProduct.objects.filter(block=self):
            if blockproduct.group not in groups:
                groups[blockproduct.group] = {'name': blockproduct.group,
                                              'products': []}
                if match and blockproduct.group == match:
                    groups[blockproduct.group]['is_visible'] = True
                elif not match and counter == 0:
                    groups[blockproduct.group]['is_visible'] = True
                else:
                    groups[blockproduct.group]['is_visible'] = False
            groups[blockproduct.group]['products'].append(blockproduct.product)
            counter += 1
        return {'groups': groups.values()}  
        
    @property
    def num_products(self):
        return self.products.all().count()
    
    @property
    def template_file(self):
        return 'promotions/block_%s.html' % self.type.lower()
    
    
class MerchandisingBlockProduct(models.Model):
    
    block = models.ForeignKey('promotions.MerchandisingBlock')
    product = models.ForeignKey('product.Item')
    group = models.CharField(_("Product group/tab"), max_length=128, blank=True, null=True)
    
    def __unicode__(self):
        return u"%s - %s (%s)" % (self.block, self.product, self.group)
    
    class Meta:
        ordering = ('group',)


class LinkedMerchanisingBlock(models.Model):

    block = models.ForeignKey('promotions.MerchandisingBlock')
    display_order = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPageMerchandisingBlock(LinkedMerchanisingBlock):
    u"""
    A promotion embedded on a particular page.
    """
    page_url = ExtendedURLField(max_length=128, db_index=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"%s on %s" % (self.block, self.page_url)
    
    
class AbstractKeywordMerchandisingBlock(LinkedMerchanisingBlock):
    u"""
    A promotion linked to a specific keyword.

    This can be used on a search results page to show promotions
    linked to a particular keyword.
    """

    keyword = models.CharField(_("Keyword"), max_length=200)

    class Meta:
        abstract = True
