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

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('main.urls')),
    path('', include('cwebsocket.urls')),
]

urlpatterns += staticfiles_urlpatterns()
