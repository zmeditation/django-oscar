from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Count
from django.utils.translation import ugettext as _

from oscar.apps.catalogue.reviews.managers import ApprovedReviewsManager
from oscar.core.compat import AUTH_USER_MODEL


class AbstractProductReview(models.Model):
    """
    Superclass ProductReview.

    Some key aspects have been implemented from the original spec.
    * Each product can have reviews attached to it. Each review has a title, a
      body and a score from 0-5.
    * Signed in users can always submit reviews, anonymous users can only
      submit reviews if a setting OSCAR_ALLOW_ANON_REVIEWS is set to true - it
      should default to false.
    * If anon users can submit reviews, then we require their name, email
      address and an (optional) URL.
    * By default, reviews must be approved before they are live.
      However, if a setting OSCAR_MODERATE_REVIEWS is set to false,
      then they don't need moderation.
    * Each review should have a permalink, ie it has its own page.
    * Each reviews can be voted up or down by other users
    * Only signed in users can vote
    * A user can only vote once on each product once
    """

    # Note we keep the review even if the product is deleted
    product = models.ForeignKey(
        'catalogue.Product', related_name='reviews', null=True,
        on_delete=models.SET_NULL)

    # Scores are between 0 and 5
    SCORE_CHOICES = tuple([(x, x) for x in range(0, 6)])
    score = models.SmallIntegerField(_("Score"), choices=SCORE_CHOICES)

    title = models.CharField(max_length=255, verbose_name=_("Review title"))
    body = models.TextField(_("Body"))

    # User information.  We include fields to handle anonymous users
    user = models.ForeignKey(
        AUTH_USER_MODEL, related_name='reviews', null=True, blank=True)
    name = models.CharField(_("Name"), max_length=255, null=True, blank=True)
    email = models.EmailField(_("Email"), null=True, blank=True)
    homepage = models.URLField(_("URL"), null=True, blank=True)

    FOR_MODERATION, APPROVED, REJECTED = range(0, 3)
    STATUS_CHOICES = (
        (FOR_MODERATION, _("Requires moderation")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
    )
    default_status = FOR_MODERATION if settings.OSCAR_MODERATE_REVIEWS else APPROVED
    status = models.SmallIntegerField(
        _("Status"), choices=STATUS_CHOICES, default=default_status)

    # Denormalised vote totals
    total_votes = models.IntegerField(
        _("Total Votes"), default=0)  # upvotes + down votes
    delta_votes = models.IntegerField(
        _("Delta Votes"), default=0, db_index=True)  # upvotes - down votes

    date_created = models.DateTimeField(auto_now_add=True)

    # Managers
    objects = models.Manager()
    approved = ApprovedReviewsManager()

    class Meta:
        abstract = True
        ordering = ['-delta_votes']
        unique_together = (('product', 'user'),)
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')

    @models.permalink
    def get_absolute_url(self):
        return ('catalogue:reviews-detail', (), {
            'product_slug': self.product.slug,
            'product_pk': self.product.id,
            'pk': self.id})

    def __unicode__(self):
        return self.title

    def clean(self):
        if not self.user and not (self.name and self.email):
            raise ValidationError(
                _("Anonymous review must have a name and an email"))

    def clean_title(self):
        title = self.title.strip()
        if not title:
            raise ValidationError(_("This field is required"))
        excess = len(title) - 100
        if excess > 0:
            raise ValidationError(
                _("Please enter a shorter title (with %d fewer characters)") %
                excess)
        return title

    def clean_body(self):
        body = self.body.strip()
        if not body:
            raise ValidationError(_("This field is required"))

    def clean_name(self):
        return self.name.strip()

    def save(self, *args, **kwargs):
        super(AbstractProductReview, self).save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        super(AbstractProductReview, self).delete(*args, **kwargs)
        self.product.update_rating()

    @property
    def has_votes(self):
        return self.total_votes > 0

    @property
    def num_up_votes(self):
        """Returns the total up votes"""
        return int((self.total_votes + self.delta_votes) / 2)

    @property
    def num_down_votes(self):
        """Returns the total down votes"""
        return int((self.total_votes - self.delta_votes) / 2)

    def update_totals(self):
        """
        Update total and delta votes
        """
        result = self.votes.aggregate(
            score=Sum('delta'), total_votes=Count('id'))
        self.total_votes = result['total_votes'] or 0
        self.delta_votes = result['score'] or 0
        self.save()

    def get_reviewer_name(self):
        if self.user:
            name = self.user.get_full_name()
            return name if name else _('anonymous')
        else:
            return self.name

    def user_may_vote(self, user):
        return (user.is_authenticated() and
                self.user != user and
                not self.votes.filter(user=user).exists())


class AbstractVote(models.Model):
    """
    Records user ratings as yes/no vote.
    * Only signed-in users can vote.
    * Each user can vote only once.
    """
    review = models.ForeignKey('reviews.ProductReview', related_name='votes')
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='review_votes')
    UP, DOWN = 1, -1
    VOTE_CHOICES = (
        (UP, _("Up")),
        (DOWN, _("Down"))
    )
    delta = models.SmallIntegerField(_('Delta'), choices=VOTE_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-date_created']
        unique_together = (('user', 'review'),)
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')

    def __unicode__(self):
        return u"%s vote for %s" % (self.delta, self.review)

    def save(self, *args, **kwargs):
        super(AbstractVote, self).save(*args, **kwargs)
        self.review.update_totals()
