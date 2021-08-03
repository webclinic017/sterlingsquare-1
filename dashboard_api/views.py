from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
# from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from accounts.models import *
from .dashboard_api_serializer import *
from rest_framework.permissions import AllowAny


# from rest_framework.authentication import TokenAuthentication, BasicAuthentication
# from rest_framework.permissions import IsAuthenticated


class DashboardApiLogin(APIView):
    def post(self, request):
        """
        login with email and password
        Parameters
        ----------
        request
        Returns
        -------
        """
        if User.objects.filter(email=request.data['email']):
            try:
                check = User.objects.get(email=request.data['email'])
                if check_password(request.data["password"], check.password):
                    token = Token.objects.get(user=User.objects.get(email=request.data["email"]))
                    return Response({"token": str(token)}, status=status.HTTP_200_OK)
                else:
                    temp = [{"message": "Incorrect Password"}]
                    return Response(temp, status=status.HTTP_404_NOT_FOUND)
            except:
                temp = [{"message": "Incorrect Email or Password"}]
                return Response(temp, status=status.HTTP_404_NOT_FOUND)

        else:
            temp = [{"message": "Incorrect Email"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


class DashboardApiGetRealisedUnrealisedGainLoss(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        get realised and unrealised gain loss of user
        Parameters
        ----------
        request
        format
        Returns
        -------
        """
        try:
            auth = request.headers.get('Authorization')
            token = Token.objects.get(key=auth.replace("Token ", ""))
            result = GainLossHistory.objects.filter(userid=token.user_id)
            serializer = GainLossHistorySerializer(result, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            temp = [{"message": "data not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


class DashboardApiGetBuyingPower(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        get buying power of user
        Parameters
        ----------
        request
        format
        Returns
        -------
        """
        try:
            try:
                auth = request.headers.get('Authorization')
                token = Token.objects.get(key=auth.replace("Token ", ""))
                res = UserDetails.objects.get(user=token.user_id)
                result = IdentityDetails.objects.filter(id=res.id)
                serializer = IdentityDetailsSerializer(result, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except:
                temp = [{"message": "data not found"}]
                return Response(temp, status=status.HTTP_404_NOT_FOUND)
        except:
            temp = [{"message": "not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)
