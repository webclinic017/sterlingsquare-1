from django.contrib import admin

# Register your models here.
from accounts.models import *

admin.site.register(UserDetails)
admin.site.register(ZerodhaCredentials)
admin.site.register(BasicDetails)
admin.site.register(IdentityDetails)
admin.site.register(Transaction)
admin.site.register(Position)
admin.site.register(Portolfio)
admin.site.register(StockHistory)
admin.site.register(StockNames)
admin.site.register(StockGeneral)
admin.site.register(TopSearched)
admin.site.register(GainLossHistory)
admin.site.register(TotalGainLoss)
admin.site.register(GainLossChartData)
# admin.site.register(StockInfo)
