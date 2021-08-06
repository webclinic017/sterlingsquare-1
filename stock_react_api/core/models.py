from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin
from django.conf import settings
from django.contrib.auth.models import User

# class UserManager(BaseUserManager):
#
#     def create_user(self, email, password=None, **extra_fields):
#         """Creates new user"""
#         if not email:
#             raise ValueError('Email address is required')
#         user = self.model(email=self.normalize_email(email), **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#
#         return user
#
#     def create_superuser(self, email, password):
#         """Creates new super user"""
#         user = self.create_user(email, password)
#         user.is_staff = True
#         user.is_superuser = True
#         user.save(using=self._db)
#
#         return user


# class User(AbstractBaseUser, PermissionsMixin):
#     """Custom user model"""
#     email = models.EmailField(max_length=200, unique=True)
#     name = models.CharField(max_length=250)
#     active_portfolio = models.IntegerField(default = 0)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#
#     objects = UserManager()
#
#     USERNAME_FIELD = 'email'

class portfolio(models.Model):
    """Portfolio Model mapped with user"""
    name = models.CharField(max_length=90, default= "")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio')

    def __str__(self):
        return "{0} - {1}".format(self.user.email, self.name)

class my_stocks(models.Model):
    """Stocks Model mapped with a portfolio"""
    portfolio = models.ForeignKey(portfolio, on_delete=models.CASCADE, related_name='stock', default = "")
    instrument_token = models.CharField(max_length=80)
    tradingsymbol = models.CharField(max_length=80)
    name = models.CharField(max_length=80, null=True, blank=True)
    buy_price = models.CharField(max_length=80, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return "{0} - {1} - {2}".format(self.portfolio.user.email, self.portfolio.name, self.tradingsymbol)