from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import InstrumentList
from import_export import fields, resources, widgets

class InstrumentListResource(resources.ModelResource):
    expiry = fields.Field(attribute='expiry', column_name='expiry', widget=widgets.DateWidget('%Y-%m-%d'))
    class Meta:
        model = InstrumentList
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)
        import_id_fields = ('instrument_token', 'exchange_token', 'tradingsymbol', \
        'name')


@admin.register(InstrumentList)
class InstrumentListAdmin(ImportExportModelAdmin):
    resource_class = InstrumentListResource
    list_display = ('instrument_token', 'tradingsymbol')
    list_filter = ('instrument_token',)
