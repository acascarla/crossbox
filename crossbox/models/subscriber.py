import datetime

from django.db import models
from django.contrib.auth.models import User

from crossbox.models.fee import Fee


class Subscriber(models.Model):
    class Meta:
        verbose_name = 'Abonado'

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='subscriber')
    wods = models.IntegerField(default=0)
    fee = models.ForeignKey(
        Fee, on_delete=models.PROTECT, null=True, blank=True,
        related_name='subscribers')
    stripe_customer_id = models.CharField('ID Cliente Stripe', max_length=30)
    stripe_subscription_id = models.CharField(
        'ID Subscripción Stripe', blank=False, null=True, max_length=30)
    stripe_billing_cycle_anchor = models.IntegerField(
        'Timestamp próximo pago', blank=True, null=True)

    def __str__(self):
        return '#{} - {}'.format(self.id, self.user)

    def username(self):
        return self.user.username

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def next_billing_cycle_datetime_property(self):
        return datetime.datetime.fromtimestamp(
            self.stripe_billing_cycle_anchor
        ) if self.stripe_billing_cycle_anchor else None

    next_billing_cycle_datetime_property.short_description = (
        "Fecha próximo cobro")
    next_billing_cycle_datetime = property(
        next_billing_cycle_datetime_property)
