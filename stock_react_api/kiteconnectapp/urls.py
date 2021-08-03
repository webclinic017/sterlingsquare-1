from django.urls import path, include
from .views import home, upload
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('portfolio', views.MyPortfolio) #List my portfolios

urlpatterns = [
    #All Links
    path('', home),
    #Include router.urls
    path('dashboard/me/', include(router.urls)),
    #View or delete requested portfolio depending on action
    path('dashboard/my_stocks/', views.Dashboard_mystocks.as_view(), name='dashboard_mystocks'),
    #Get historical data of requested stock
    path('dashboard/history/', views.HistoryDataView.as_view(), name='history'), 
    #Create a new portfolio with a file attached and portfolio_name
    path('dashboard/upload/', views.FileUploadViewSet.as_view(), name='upload'),
    #Get errors while creating a new portfolio with a file attached and portfolio_name
    path('dashboard/upload_err/', views.FileUploadErrViewSet.as_view(), name='upload_err'),
    path('dashboard/uploadd/', views.upload),

]
