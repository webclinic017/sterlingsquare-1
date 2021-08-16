from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from stock_react_api.core import models
from django.utils.translation import gettext as _

#
# class UserAdmin(BaseUserAdmin):
#     ordering = ['id']
#     list_display = ['email', 'name']
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         (_('Personal Info'), {'fields': ('name', 'active_portfolio')}),
#         (
#             _('Permissions'),
#             {'fields': ('is_active', 'is_staff', 'is_superuser')}
#         ),
#         (_('Important dates'), {'fields': ('last_login',)})
#     )
#
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password1', 'password2')
#         }),
#     )


# admin.site.register(models.User, UserAdmin)
admin.site.register(models.my_stocks)
admin.site.register(models.portfolio)