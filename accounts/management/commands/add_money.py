from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect

from accounts.models import UserDetails
from django.contrib.auth.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        email = input("Email: ")
        if email:
            try:
                u = User.objects.get(email__iexact=email)
                try:
                    details = UserDetails.objects.get(user=u)
                except Exception as e:
                    print("User details not found", e)
                    exit()

                identity = details.identity
                buying_power = identity.buyingpower
                print("User Details ... ")
                print(f"Email: {u.email}")
                print(f"Buying Power Now: {buying_power}")

                amount = float(input("Amount to be added to the account (INR):"))
                buying_power = float(buying_power) + amount

                identity.buyingpower = buying_power
                identity.save()
                details.save()
            except Exception as e:
                print(f"User {email} not found")
                exit()
        else:
            print(f"Invalid Email {email}")
            exit()
