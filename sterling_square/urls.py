import debug_toolbar
from django.contrib import admin
from django.urls import path, include
from .views import *
# from sterling_square import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = [
    # URLs are to be used by the
    # path("auto/login", auto_login),
    path('debug', include(debug_toolbar.urls)),
    path("singleton", start_singleton),
    path("initialize", initialize),
    path('auth/step_1', auth_step_1),
    path('auth/step_2', auth_step_2),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('main.urls')),
    path('', include('cwebsocket.urls')),
    path('', include('dashboard_api.urls')),
    path('', include('stock_react_api.kiteconnectapp.urls')),
    path('user/', include('stock_react_api.user.urls')),  # For user registeration and login
]

urlpatterns += staticfiles_urlpatterns()
