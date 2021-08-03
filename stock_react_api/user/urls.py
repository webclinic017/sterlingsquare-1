from django.urls import path

from stock_react_api.user import views


app_name = 'user'

urlpatterns = [
    path('register/', views.CreateUserView.as_view(), name='create'),
    path('login/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
]
