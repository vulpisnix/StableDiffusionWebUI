from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.urls import path
from django.views import View

from SDWebUI import settings
from web.models import Settings


class ViewRegister(View):
    template_name = 'auth/register.html'

    def get(self, request):
        if Settings.objects.get(name="allow_register").value == "false": return render(request,
                                                                                       'auth/register_disabled.html')
        form = UserCreationForm()
        return render(request, self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if Settings.objects.get(name="allow_register").value == "false": return render(request,
                                                                                       'auth/register_disabled.html')
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            form.save()

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(settings.LOGIN_REDIRECT_URL)
        return render(request, self.template_name, context={'form': form})


class ViewLogin(View):
    template_name = 'auth/login.html'

    def get(self, request):
        form = AuthenticationForm()
        return render(request, self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(settings.LOGIN_REDIRECT_URL)

        return render(request, self.template_name, context={'form': form})


class ViewLogout(View):
    def get(self, request):
        logout(request)
        return redirect(settings.LOGOUT_REDIRECT_URL)

    def post(self, request):
        self.get(request)


urlpatterns = [
    path('register/', ViewRegister.as_view(), name='auth_register'),
    path('login/', ViewLogin.as_view(), name='auth_login'),
    path('logout/', ViewLogout.as_view(), name='auth_logout'),
]
