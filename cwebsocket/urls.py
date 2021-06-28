from django.urls import path

from . import views

urlpatterns = [
    path('ws/wbs', views.index, name='index'),
]