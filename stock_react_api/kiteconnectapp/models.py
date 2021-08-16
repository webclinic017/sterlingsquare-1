from django.db import models

class InstrumentList(models.Model):
    id = models.AutoField(primary_key=True)
    instrument_token = models.CharField(max_length=80)
    exchange_token = models.CharField(max_length=80)
    tradingsymbol = models.CharField(max_length=80)
    name = models.CharField(max_length=80, null=True, blank=True)
    

    def __str__(self):
        return "{0} -- {1}".format(self.instrument_token, self.tradingsymbol)
