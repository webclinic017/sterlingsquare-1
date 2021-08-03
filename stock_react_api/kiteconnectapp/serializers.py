from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
# from tickerstore.store import TickerStore
from datetime import date
from stock_react_api.core.models import my_stocks, portfolio

class HistoryDataSerializer(serializers.Serializer):

    symbol = serializers.CharField(max_length=50)
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    interval_in_days = serializers.IntegerField(required=False)

class FileSerializer(serializers.Serializer):
    portfolio_name = serializers.CharField(max_length=50)
    file = serializers.FileField(max_length=None, allow_empty_file=False)
    
class StockSerializer(serializers.Serializer):
    """Serializer for tag objects"""
    portfolio_name = serializers.CharField(max_length=50)
    action = serializers.CharField(max_length=50)   

class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = portfolio
        fields = ('name',)
        read_only_fields = ('id',)
