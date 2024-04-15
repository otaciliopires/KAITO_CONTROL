from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Ordem_Oficina
from .models import Equipamentos
from django.db.models import Max

# Create your views here.


def home_manutencao(request):

    if request.method == 'GET':
        list_equip=[]
        equipamentos_rocha = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        for i in equipamentos_rocha:
            list_equip.append(i)
            
        return render(request, 'home_manutencao.html', {'list_equip':list_equip})

    elif request.method == 'POST':
        form_osoficina = request.POST.get('form_osoficina')

        #equipamentos da rocha

        #adquirir as informações dos forms da OS oficina.
        if form_osoficina:
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            data_inicio = request.POST.get('data_inicio')
            horimetro = request.POST.get('horimetro')

            print(equipamento, data_inicio, horimetro)
        
        #adquirir o maior numero na lista de O.S.
        numero = Ordem_Oficina.objects.aggregate(Max('numero'))['numero__max']

        #adicionar o form da oficina,o de criação de da O.S.
        osoficina = Ordem_Oficina(equipamento=equipamento,
                                     data_inicio=data_inicio,
                                     horimetro=horimetro,
                                     numero=numero+1)
        osoficina.save()



        return redirect('/manutencao/home_manutencao')

def servico_oficina(request):


    return HttpResponse('okok') 