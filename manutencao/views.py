from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Ordem_Oficina, Servico_Oficina, Grupo_Servico, Funcionario, Servico_Terceirizado
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


        #dados para OS da oficina
        os_oficina_aberta = Ordem_Oficina.objects.filter(data_fim=None)
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
    if request.method == 'GET':
        ordem_oficina_aberta = Ordem_Oficina.objects.get(id=id)
        print(ordem_oficina_aberta.equipamento)

        servico_oficina =  Servico_Oficina.objects.filter(ordem_servico=id)
        print(servico_oficina)

        grupo_servico = Grupo_Servico.objects.all()
        executantes = Funcionario.objects.all()
        terceiros = Servico_Terceirizado.objects.all()
        servicos = Servico_Oficina.objects.all()
        for servico in servicos:
            print(servico.executante)
    
        return render(request, 'os_oficina_service.html', {'ordem_oficina_aberta': ordem_oficina_aberta,
                                                       'servico_oficina': servico_oficina,
                                                       'grupo_servico': grupo_servico,
                                                       'executantes':executantes,
                                                       'terceiros': terceiros,
                                                       'id_OS_oficina':id})
    
    elif request.method == 'POST':
        form_servico = request.POST.get('form_servico')
        form_status_servico = request.POST.get('form_status_servico')

        if form_servico:
            numero = Servico_Oficina.objects.aggregate(Max('numero'))['numero__max']
            ordem_oficina_aberta = Ordem_Oficina.objects.get(id=id)
            grupo_servico_id = request.POST.get('grupo_servico')
            grupo_servico = Grupo_Servico.objects.get(id=grupo_servico_id)
            data_inicio = request.POST.get('data_inicio')
            status_executante = request.POST.get('status_executante')
            descricao_servico = request.POST.get('descricao')
            if status_executante == 'funcionario':
                funcionario_id = request.POST.get('executante_funcionario')
                terceiro = None
                funcionario = Funcionario.objects.get(id=funcionario_id)
            else:
                funcionario= None
                terceiro_id = request.POST.get('executante_terceiro')
                terceiro = Servico_Terceirizado.objects.get(id=terceiro_id)
            

        servico_oficina = Servico_Oficina(numero=numero+1,
                                          ordem_servico=ordem_oficina_aberta,
                                          grupo_servico=grupo_servico,
                                          data_inicio=data_inicio,
                                          descricao = descricao_servico,
                                          executante_terceiro=terceiro,
                                          executante_funcionario=funcionario)
        
        servico_oficina.save()

    elif form_status_servico:

                
        print(grupo_servico_id, data_inicio, status_executante, funcionario, terceiro, descricao_servico)
    

    

 
    return HttpResponse(f'Serviço cadastrado com sucesso :D  {grupo_servico, data_inicio, status_executante, descricao_servico}')