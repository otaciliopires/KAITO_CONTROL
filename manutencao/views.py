from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def home_manutencao(request):

    if request.method == 'GET':
        return render(request, 'home_manutencao.html')

    elif request.method == 'POST':
        form_osoficina = request.POST.get('form_osoficina')

        if form_osoficina:
            #adquirir as informações dos forms da OS oficina.
            



            return HttpResponse("funcionou")