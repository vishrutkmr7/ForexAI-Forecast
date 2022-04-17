from django.db import models
from django.urls import reverse
import requests

# Create your models here.
class dataForm(models.Model):
    # Need to convert X USD to INR
    base_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    amount = models.IntegerField()
    max_waiting_time = models.IntegerField()
    start_date = models.DateField(auto_now_add=True)

    # Other data
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        ordering = ['-start_date']

        def __unicode__(self):
            return f'{self.title}'

    def get_absolute_url(self):
        return reverse('forecaster.views.home', args=[self.slug])
