from rest_framework import serializers
from accounts.models import *


class GainLossHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GainLossHistory
        fields = ('userid', 'unrealised_gainloss', 'realised_gainloss')


class IdentityDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityDetails
        fields = ('id', 'buyingpower')
