from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.messages import constants


def login(request):
    if request.user.is_authenticated and (request.user.status == 'a' or getattr(settings, 'AMBIENTE_HOMOLOGACAO', False)):
        return redirect('campo')

    if request.method == 'GET':
        if request.user.is_authenticated and request.user.status == 'c':
            return redirect('home')
        elif request.user.is_authenticated and request.user.status == 'o':
            return redirect('lista_obras')
        else:
            return render(request, 'login.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        senha = request.POST.get('password')

        user = auth.authenticate(username=username, password=senha)

        if not user:
            messages.add_message(request, constants.ERROR, 'Usuário ou senha inválidos')
            return redirect('login')

        auth.login(request, user)
        if user.status == 'a' or getattr(settings, 'AMBIENTE_HOMOLOGACAO', False):
            return redirect('campo')
        if request.user.status == 'c':
            return redirect('home')
        return redirect('lista_obras')


def sair(request):
    auth.logout(request)
    return redirect('login')
