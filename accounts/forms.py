from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms import forms, ModelForm
from django.utils.translation import ugettext, ugettext_lazy as _
from accounts.models import IdentityDetails, BasicDetails, UserDetails
from django import forms as django_form


class CustomAuthForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        print("USERNAME     ", username, password)
        if username is not None and password:
            self.user_cache = authenticate(self.request, email=username,
                                           password=password)
            print(username, "????????")
            if self.user_cache is None:
                try:
                    user_temp = User.objects.get(email=username)
                except:
                    user_temp = None

                if user_temp is not None and user_temp.check_password(
                        password):
                    self.confirm_login_allowed(user_temp)
                else:
                    raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                        params={'username': self.username_field.verbose_name},
                    )

        return self.cleaned_data


class UserDetailsForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name',
                  'last_name',
                  'email'
                  ]


class BasicDetailsForm(ModelForm):
    class Meta:
        model = BasicDetails
        fields = ['residential_address1',
                  'residential_address2',
                  'city',
                  'state',
                  'zipcode',
                  'phone_number',
                  ]


class IdentityDetailsForm(ModelForm):
    class Meta:
        model = IdentityDetails
        fields = ['dob',
                  'ssn',
                  'citizenship',
                  'marital_status',
                  'dependents',
                  'investment_experience',
                  'employment_status'
                  ]

# class LoginForm(forms.Form):
#     email = django_form.CharField(max_length=254)
#     password = django_form.CharField(label=_("password"),
#     widget=django_form.PasswordInput)
#     def clean(self):
#         print(">   <   ",self.cleaned_data)
#         username = self.cleaned_data.get('email')
#         password = self.cleaned_data.get('password')
#         print("?>   ",username,password)
#         if username is not None and password:
#             self.user_cache = authenticate(self.request,
#             username=username, password=password)
#             print(">  ",UserDetails.objects.get(email=username))
#             if self.user_cache is None:
#                 try:
#                     user_temp = UserDetails.objects.get(email=username)
#                 except:
#                     user_temp = None
#
#                 if user_temp is not None and user_temp.check_password(
#                 password):
#                     self.confirm_login_allowed(user_temp)
#                 else:
#                     raise forms.ValidationError(
#                         self.error_messages['invalid_login'],
#                         code='invalid_login',
#                         params={'username':
#                         self.username_field.verbose_name},
#                     )
#
#         return self.cleaned_data
