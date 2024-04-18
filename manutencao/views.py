from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Ordem_Oficina
from .models import Equipamentos
from django.db.models import Max
from datetime import datetime
from manutencao.utils import now

# Create your views here.


def home_manutencao(request):

    if request.method == 'GET':
        list_equip=[]
        equipamentos_rocha = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        for i in equipamentos_rocha:
            list_equip.append(i)


        #atualização de status manutenção
        list = []
        os_oficina_aberta = Ordem_Oficina.objects.filter(data_fim=None)
        for i in os_oficina_aberta:
            print(i.status)

        #dados para OS da oficina
        os_oficina_aberta = Ordem_Oficina.objects.filter(data_fim=None)
        print(os_oficina_aberta[0].id)
        return render(request, 'home_manutencao.html', {'list_equip':list_equip,
                                                        'os_oficina_aberta':os_oficina_aberta})

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

def servico_oficina(request, id):

    ordem_oficina_aberta = Ordem_Oficina.objects.get(id=id)
    print(ordem_oficina_aberta.equipamento)

    


    return render(request, 'os_oficina_service.html', {'ordem_oficina_aberta': ordem_oficina_aberta})