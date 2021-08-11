from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/api/portfolio/historical/', views.DashboardHistoricalAPI.as_view(), name='dashboard-api'),
    path('dashboard/stock-search/', views.StockSearchView.as_view(),
         name='stock_search'),
    path('dashboard/stocks/<str:stock_symbol>/', views.StockPageView.as_view(),
         name='stocks'),
    path('dashboard/api/stocks/', views.StockPageAPI.as_view()),
    path('dashboard/api/stock_summary/', views.GetStocksAPI.as_view()),
    path('dashboard/api/watchlist/', views.GetWatchListAPI.as_view()),
    path('dashboard/api/most_active/', views.GetTopGainers.as_view()),
    path('dashboard/api/market_values/<str:symbol>', views.MarketValuesAPI.as_view()),
    path('dashboard/api/transactions/', views.PositionTableAPI.as_view()),
    path('dashboard/api/upcoming_activity/<str:symbol>', views.GetUpcomingActivityAPI.as_view()),
    path('dashboard/api/historical/', views.StockPageHistoricalAPI.as_view()),
    path('update-stock-data/', views.UpdateStockScheduler.as_view(),
         name='stock_schedule'),
    path('position-table/', views.PositionTablesDetailsView.as_view(),
         name='position_table'),
    path('latest-gain-loss/', views.GetLatestGainLossView.as_view(),
         name='top_gainers'),
    path('logout/', views.logout_user, name='logout'),
    path('buyingpower/', views.UpdateBuyingPower.as_view(), name='buyingpower'),
]
