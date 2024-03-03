from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import auth
from django.contrib import messages
from django.contrib.messages import constants

# Create your views here.


def login(request):
    
    if request.method == 'GET':
        return render(request,'login.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        senha = request.POST.get('password')
        status = request.POST.get('status')

        user = auth.authenticate(username=username,
                            password=senha
                                )
        
        if not user:
            messages.add_message(request, constants.ERROR, 'Usuário ou senha inválidos')
            return redirect('/auth/login')
        
        else:
            auth.login(request, user)
            if request.user.status == 'c':

                return redirect('/ceq/home')
            else:
                userid = request.user.id
                return(redirect(f'/obra/lista_obras'))
            
def sair(request):
    auth.logout(request)
    return redirect('/auth/login')
            




    