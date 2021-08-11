from django.urls import path, include
from . import views

urlpatterns = [
    path('dashboard_api_login/', views.DashboardApiLogin.as_view()),
    path('dashboard_api_get_buying_power/', views.DashboardApiGetBuyingPower.as_view()),
    path('dashboard_api_get_realised_unrealised_gain_loss/', views.DashboardApiGetRealisedUnrealisedGainLoss.as_view()),
    # path('dashboard_api_portfolio_performance_stock/', views.DashboardApiPortfolioPerformanceStock.as_view()),
    path('dashboard_api_sectorwise_data/', views.DashboardApiSectorWiseData.as_view()),
    path('dashboard_api_testing/', views.DashboardApiTesting.as_view()),

]
