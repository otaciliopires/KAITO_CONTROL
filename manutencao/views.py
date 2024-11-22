from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Ordem_Oficina, Servico_Oficina, Grupo_Servico, Funcionario, Servico_Terceirizado, Solicitacao, Socorro, Servico_Socorro, Preventiva, Ordem_Preventiva, Servico_Preventiva, Registro_Tempo_Servico
from .models import Equipamentos, Obras
from django.db.models import Max
from datetime import datetime, timezone, date, timedelta
from manutencao.utils import now, att_tempo_2, att_tempo_1_os, att_tempo_1_servico, hora_correta
from django.db.models import Sum, Max

# Create your views here.


def home_manutencao(request):

    if request.method == 'GET':
        list_equip=[]
        equipamentos_rocha = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        obras = Obras.objects.all()
        print("xxxxxxxxxx", obras, equipamentos_rocha)
        for i in equipamentos_rocha:
            list_equip.append(i)
        print(list_equip)
        
        
        #TRATAMENTO  OS CORRETIVAS
        ordens = Ordem_Oficina.objects.all()        
        os_oficina_abertas = Ordem_Oficina.objects.filter(data_fim=None)  
        num_servicos_abertos = []
        num_servicos_finalizados= []
        status_serv = []
        lista_servicos_a = []
        lista_servicos_f = []
        for os in os_oficina_abertas:
            servicos_finalizados = Servico_Oficina.objects.filter(ordem_servico=os, data_fim__isnull=False)
            servicos_abertos = Servico_Oficina.objects.filter(ordem_servico=os, data_fim=None)
            num_servicos_finalizados.append(servicos_finalizados.count())
            num_servicos_abertos.append(servicos_abertos.count())
            lista_servicos_a.append(servicos_abertos)
            lista_servicos_f.append(servicos_finalizados)
            if Servico_Oficina.objects.filter(ordem_servico=os, data_fim=None, status="Em Serviço").exists():
                status = "Em Serviço" 
                status_serv.append(status)
            elif Servico_Oficina.objects.filter(ordem_servico=os, data_fim=None, status="Aguardando Peças").exists():
                status = "Aguardando Peças"
                status_serv.append(status)
                pass
            else:
                status = "Aguardando Serviço"
                status_serv.append(status)
            print(status_serv)
        dados_zip = zip(os_oficina_abertas, num_servicos_finalizados, num_servicos_abertos, status_serv, lista_servicos_a, lista_servicos_f)
    
        #TRATAMENTO SOCORRO
        socorros_abertos = Socorro.objects.filter(data_chegada__isnull=True)
        qtd_serv_socorros = []
        list_equipamentos = []
        list_servicos_socorro = []
        for socorro_aberto in socorros_abertos:
            serv_socorro = Servico_Socorro.objects.filter(socorro = socorro_aberto.id)
            equips = []
            list_servicos_socorro.append(serv_socorro)
            for serv in serv_socorro:
                equips.append(serv.equipamento.prefixo)
            list_equipamentos.append(equips)    

            qtd_serv_socorros.append(serv_socorro.count())

        dados_socorro = zip(socorros_abertos,qtd_serv_socorros, list_equipamentos, list_servicos_socorro )


        #Tratamento PREVENTIVAS
        equipamentos_preventiva= Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        preventivas = Preventiva.objects.filter(data_fim=None)




        return render(request, 'home_manutencao.html', {'list_equip':list_equip,
                                                    'os_oficina_aberta':os_oficina_abertas,
                                                    'dados_zip':dados_zip,
                                                    'serv_a':lista_servicos_a,
                                                    'serv_f':lista_servicos_f,
                                                    'obras':obras, 
                                                    'dados_zip_socorro':dados_socorro,
                                                    'equipamentos_preventiva':equipamentos_preventiva,
                                                    'preventivas':preventivas
                                                
                                                    })

    elif request.method == 'POST':
        form_osoficina = request.POST.get('form_osoficina')
        form_socorro = request.POST.get('form_socorro')
        form_preventiva = request.POST.get('form_preventiva')

        #equipamentos da rocha

        #adquirir as informações dos forms da OS oficina.
        if form_osoficina:
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            data_inicio = request.POST.get('data_inicio')
            horimetro = request.POST.get('horimetro')
        
            #adquirir o maior numero na lista de O.S.
            if Ordem_Oficina.objects.aggregate(Max('numero'))['numero__max'] == None:
                numero = 0
            else:
                numero = Ordem_Oficina.objects.aggregate(Max('numero'))['numero__max']

            #adicionar o form da oficina,o de criação de da O.S.
            osoficina = Ordem_Oficina(equipamento=equipamento,
                                        data_inicio=data_inicio,
                                        data_status=data_inicio,
                                        horimetro=horimetro,
                                        numero=numero+1)
            osoficina.save()

            return redirect('/manutencao/home_manutencao')
    
        if form_socorro:
            obra_id = request.POST.get('obra')
            obra = Obras.objects.get(id=obra_id) 
            data_saida = request.POST.get('data_saida')
            if Socorro.objects.aggregate(Max('numero'))['numero__max'] == None:
                numero = 0
            else:
                numero = Socorro.objects.aggregate(Max('numero'))['numero__max']

            socorro = Socorro(obra = obra,
                              data_saida = data_saida,
                              numero = numero+1,
                              data_chegada = None)
            
            socorro.save()
            
            
            return redirect('/manutencao/home_manutencao')
        
        if form_preventiva:
            obra_id = request.POST.get('obra')
            obra = Obras.objects.get(id=obra_id)
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            data_emissao = request.POST.get('data_emissao')
            periodo = int(request.POST.get('periodo'))
            ordem = Ordem_Preventiva.objects.get(equipamento=equipamento, periodo=periodo)
            if Preventiva.objects.aggregate(Max('numero'))['numero__max'] == None:
                    numero = 0
            else:
                    numero = Preventiva.objects.aggregate(Max('numero'))['numero__max']

            preventiva = Preventiva(local = obra,
                                    ordem = ordem ,
                                    data_emissao=data_emissao,
                                    numero=numero+1)
            
            preventiva.save()


            return redirect('/manutencao/home_manutencao')


def servico_oficina(request, id):
    if request.method == 'GET':
        if Ordem_Oficina.objects.all().exists():
            ordem_oficina_aberta = Ordem_Oficina.objects.get(id=id)
        else:
            return redirect("/manutencao/home_manutencao") 

        servico_oficina = Servico_Oficina.objects.filter(ordem_servico = id)
        for service in servico_oficina:

            if service.status == "Em Serviço":

                break
            elif service.status == "Aguardando Peças": # de todos os aguardando peças, somar o com a data mais antiga.
                print(service.data_mudanca_status) 
        

        grupo_servico = Grupo_Servico.objects.all()
        executantes = Funcionario.objects.all()
        terceiros = Servico_Terceirizado.objects.all()


        servicos = Servico_Oficina.objects.all()
        for servico in servicos:
            print(servico.tempo_aguardo_servico)
        return render(request, 'os_oficina_service.html', {'ordem_oficina_aberta': ordem_oficina_aberta,
                                                       'servico_oficina': servico_oficina,
                                                       'grupo_servico': grupo_servico,
                                                       'executantes':executantes,
                                                       'terceiros': terceiros,
                                                       'id_OS_oficina':id})

    
    elif request.method == 'POST':
        form_servico = request.POST.get('form_servico')
        form_status_servico = request.POST.get('form_status_servico')
        form_fim_os = request.POST.get('form_fim_os')

        if form_servico: #FORMULÁRIO DE ADIÇÃO DE SERVIÇO
            ordem_oficina_aberta = Ordem_Oficina.objects.get(id=id)
            grupo_servico_id = request.POST.get('grupo_servico')
            grupo_servico = Grupo_Servico.objects.get(id=grupo_servico_id)
            data_inicio = request.POST.get('data_inicio')
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%dT%H:%M")
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
            
            numero = Servico_Oficina.objects.aggregate(Max('numero'))['numero__max']
            if numero == None:
                numero = 0
            else:pass
            
            servico_oficina = Servico_Oficina(numero=numero+1,
                                          status= 'Em Serviço',
                                          ordem_servico=ordem_oficina_aberta,
                                          grupo_servico=grupo_servico,
                                          data_inicio=data_inicio,
                                          data_mudanca_status=data_inicio,
                                          descricao = descricao_servico,
                                          executante = status_executante,
                                          executante_terceiro=terceiro,
                                          executante_funcionario=funcionario)
            
            att_tempo_1_os(ordem_oficina_aberta.id, data_inicio)        
            servico_oficina.save()
            print(type(data_inicio), data_inicio)

            #Criação de objeto registro de mecanico - tempo serviço
            registro_tempo_servico = Registro_Tempo_Servico(servico_oficina=servico_oficina,
                                                                    funcionario= funcionario,
                                                                    tercerizado = terceiro,
                                                                    data_inicial = data_inicio,
                                                                    descricao = descricao_servico
                                                                    )
            registro_tempo_servico.save()

            return redirect(f"/manutencao/osoficina/{ordem_oficina_aberta.id}")



        if form_status_servico:#FORMULÁRIO DE ALTERAÇÃO DE STATUS DE SERVIÇO
            id_servico = request.POST.get("id_servico")
            servico_oficina = Servico_Oficina.objects.get(id=id_servico)
            
            data_fim = request.POST.get('data_fim')



            if data_fim == "":
                data_status = request.POST.get('data_status')
                data_status = datetime.strptime(data_status, "%Y-%m-%dT%H:%M")          
                pass
            else:
                data_fim = datetime.strptime(data_fim, "%Y-%m-%dT%H:%M")
                servico_oficina.data_fim = data_fim
                data_status = data_fim
            att_tempo_1_os(id, data_status)
            status_servico = request.POST.get('status_servico')   
            executante_funcionario_id = request.POST.get('executante_funcionario')
            if executante_funcionario_id == None:
                executante_funcionario = None
            else:
                executante_funcionario = Funcionario.objects.get(id=executante_funcionario_id)
            
            executante_terceiro_id = request.POST.get('executante_terceiro')
            if executante_terceiro_id == None:
                executante_terceiro = None
            else:
                executante_terceiro = Servico_Terceirizado.objects.get(id=executante_terceiro_id)
           
            descricao_atual = Servico_Oficina.objects.get(id=id_servico).descricao
            descricao = descricao_atual + " - " + request.POST.get('descricao')   #descrição funcionando
           
            servico_oficina.descricao = descricao
            servico_oficina.executante_funcionario = executante_funcionario
            servico_oficina.executante_terceiro = executante_terceiro
            # servico_oficina.status = status_servico

            #FECHAR OBJETO DE REGISTRO DE TEMPO DO MECANICO - UTILIZAR SERVICO OFICINA.
            registro_tempo_servico = Registro_Tempo_Servico.objects.get(servico_oficina=servico_oficina.id, data_final=None)
            registro_tempo_servico.data_final = data_status
            registro_tempo_servico.tempo_servico = (data_status.timestamp() - registro_tempo_servico.data_inicial.timestamp())/3600
            registro_tempo_servico.save()


            if servico_oficina.status == "Em Serviço":
                    servico_oficina.tempo_em_servico += (data_status.timestamp() - servico_oficina.data_mudanca_status.timestamp())/3600                 
                    servico_oficina.tempo_total += (data_status.timestamp() - servico_oficina.data_mudanca_status.timestamp())/3600 
                    servico_oficina.data_mudanca_status = data_status
                    servico_oficina.status = status_servico
                    #CRIAR OBJETO DE REGISTRO DE TEMPO DO MECANICO
                    registro_tempo_servico = Registro_Tempo_Servico(servico_oficina=servico_oficina,
                                                                    funcionario=executante_funcionario,
                                                                    tercerizado = executante_terceiro,
                                                                    data_inicial = data_status,
                                                                    descricao = request.POST.get('descricao')
                                                                    )
                    registro_tempo_servico.save()

            elif servico_oficina.status == "Aguardando Peças":
                    servico_oficina.tempo_aguardo_peca += hora_correta(servico_oficina.data_mudanca_status, data_status)
                    servico_oficina.tempo_total += hora_correta(servico_oficina.data_mudanca_status, data_status)
                    servico_oficina.data_mudanca_status = data_status
                    servico_oficina.status = status_servico

            elif servico_oficina.status == 'Aguardando Serviço':
                    servico_oficina.tempo_aguardo_servico += hora_correta(servico_oficina.data_mudanca_status, data_status) 
                    servico_oficina.tempo_total += hora_correta(servico_oficina.data_mudanca_status, data_status)                     
                    servico_oficina.data_mudanca_status = data_status
                    servico_oficina.status = status_servico

            servico_oficina.save()
            # print(Servico_Oficina.objects.get(id=id_servico).status)
                        #colocar a função antes de salvar as informações no BD garante que o valor calculado de tempo seja contabilizado para o status anterior(correto)  
                
        
              

        
                                


        #para hoje, adicionar um datetime na mudança de status. Caso não seja adicionado esse datetime, será considerado o horário da mudança atual.
        #com esse datetime, calcular o tempo em no status selecionado. Talvez seja necessário adicionar mais uma variável no models, o datetime de mudança de status, para que
        #quando for necessário calcular o tempo em cada status, se basear o horário inicial no ultimo datetime cadastrado.


            return redirect(f'/manutencao/osoficina/{id}')
        
        if form_fim_os:

            data_fim = request.POST.get('data_fim')
            os_oficina = Ordem_Oficina.objects.get(id=id)
            # servicos_oficina = Servico_Oficina.objects.get(id=os_oficina)
            

            #verificar se tem algum serviço em aberto, caso sim, não salvar a data e fornecer uma mensagem de erro
            os_oficina.data_fim = data_fim
            print(data_fim)
            os_oficina.save()
            return redirect('/manutencao/home_manutencao/')
            

def atualizacao_horarios(request):
    now = datetime.now(timezone.utc)
    
    if now.hour - 3 < 7 or now.hour - 3 > 17:
        pass
    else:
        os_oficina_abertas = Ordem_Oficina.objects.filter(data_fim=None)
        for os in os_oficina_abertas:
            print(os.id, os.equipamento.prefixo)

        # a = Servico_Oficina.objects.all()
        # for b in a:
        #     print(b.data_mudanca_status)
            att_tempo_1_os(os.id, now)
        print("good game", now.day, type(now.hour),now.timestamp())
        servicos_oficina_abertos = Servico_Oficina.objects.filter(data_fim=None)
        for servico_oficina in servicos_oficina_abertos:

            if servico_oficina.status == "Em Serviço":
                            servico_oficina.tempo_em_servico += (now.timestamp() - servico_oficina.data_mudanca_status.timestamp())/3600                 
                            servico_oficina.tempo_total += (now.timestamp() - servico_oficina.data_mudanca_status.timestamp())/3600 
                            servico_oficina.data_mudanca_status = now
                            servico_oficina.status = now
            elif servico_oficina.status == "Aguardando Peças":
                            servico_oficina.tempo_aguardo_peca += hora_correta(servico_oficina.data_mudanca_status, now)
                            servico_oficina.tempo_total += hora_correta(servico_oficina.data_mudanca_status, now)
                            servico_oficina.data_mudanca_status = now
                            servico_oficina.status = now

            elif servico_oficina.status == 'Aguardando Serviço':
                            servico_oficina.tempo_aguardo_servico += hora_correta(servico_oficina.data_mudanca_status, now) 
                            servico_oficina.tempo_total += hora_correta(servico_oficina.data_mudanca_status, now)                     
                            servico_oficina.data_mudanca_status = now
                            servico_oficina.status = now




        return redirect('/manutencao/home_manutencao/')





#criar uma classe chamada tempo funcionário-terceiro

#Nessa classe serão contabilizados os tempos em serviço de cada funcionário ou terceiro. Toda vez que houver uma mudança de status em um serviço será contabilizado o tempo desse funcionário 
#no serviço, o tempo no tipo de serviço
#nessa classe serão registrados todas as mudanças de serviço e contabilizados os tempos unicamente em serviço, preservando att_tempo_01, pois o att_tempo_01 contabiliza o tempo de mudança de status.


def solicitacoes(request):

    if request.method == "GET":
    
        #informaçoes das solicitações:
        solicitacoes = Solicitacao.objects.filter(atendida=False)
        equipamentos = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        compradores = Funcionario.objects.filter(funcao="Comprador")
        status = ('Selecionar','Baixa Prioridade', 'Média Prioridade', 'Alta Prioridade', 'Urgente')


        return render(request, 'solicitacoes.html', {'solicitacoes_abertas':solicitacoes,
                                                     'equipamentos':equipamentos,
                                                     'compradores':compradores,
                                                     'status':status,
                                                     })
    
    elif request.method == "POST":
        form_add_solicitacao = request.POST.get('form_solicitacao')
        form_att_solicitacao = request.POST.get('form_att_solicitacao')

        if form_add_solicitacao:
            insumo = request.POST.get('insumo')
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            comprador_id = request.POST.get('comprador')
            comprador = Funcionario.objects.get(id=comprador_id)
            solicitacao = request.POST.get('solicitacao')
            data_envio = request.POST.get('data_solicitacao')
            data_envio = datetime.strptime(data_envio, "%Y-%m-%dT%H:%M")  
            status = request.POST.get('status')
            if status=="Selecionar":
                status = 'Baixa Prioridades'
            previsao = request.POST.get('data_previsao')
            if previsao == "":
                previsao="ok"
            link = request.POST.get('link')
            observacao = request.POST.get('observacao')

            cadastro_solicitacao = Solicitacao(insumo=insumo,
                                               equipamento=equipamento,
                                               comprador=comprador,
                                               solicitacao=solicitacao,
                                               data_suprimentos=data_envio,
                                               status=status,
                                               data_previsao=previsao,
                                               link_solicitacao=link,
                                               observacao=observacao 
                                               )
            cadastro_solicitacao.save()

            return redirect('/manutencao/solicitacoes/')

        elif form_att_solicitacao:
            id_solicitacao = request.POST.get('id_solicitacao')
            solicitacao_atual = Solicitacao.objects.get(id = id_solicitacao)

            insumo = request.POST.get('insumo')
            if insumo == "":
                pass
            else:
                solicitacao_atual.insumo = insumo
            
            equipamento_id = request.POST.get('equipamento')
            if equipamento_id == 'equipamento':
                equipamento = None
            else:
                equipamento = Equipamentos.objects.get(id=equipamento_id)
                solicitacao_atual.equipamento = equipamento
            
            comprador_id = request.POST.get('comprador')
            if comprador_id == 'comprador':
                comprador = None
            else:
                comprador = Funcionario.objects.get(id=comprador_id)
                solicitacao_atual.comprador = comprador

            solicitacao = request.POST.get('solicitacao')    
            if solicitacao == "":
                pass
            else:
                solicitacao_atual.solicitacao = solicitacao

            data_envio = request.POST.get('data_solicitacao')
            if data_envio == "":
                pass
            else:   
                data_envio = datetime.strptime(data_envio, "%Y-%m-%dT%H:%M")  
                solicitacao_atual.data_suprimentos = data_envio

            status = request.POST.get('status')
            if status == "Selecionar":
                pass
            else:
                solicitacao_atual.status = status

            previsao = request.POST.get('data_previsao')
            if previsao == "":
                pass
            else:
                solicitacao_atual.data_previsao = previsao
            
            link = request.POST.get('link')
            if link == "":
                pass
            else:
                solicitacao_atual.link_solicitacao = link
            
            observacao = request.POST.get('observacao')
            if observacao == "":
                pass
            else:
                solicitacao_atual.observacao = observacao
            
            atendida = request.POST.get('atendido')
            if atendida != True:
                atendida = False
            solicitacao_atual.atendida = atendida
            print(insumo, id_solicitacao, equipamento_id, comprador_id,solicitacao, data_envio, status, previsao, observacao, atendida)
            print("xxxxxx", data_envio)

            solicitacao_atual.save()

            return redirect('/manutencao/solicitacoes/')

def socorro(request, id):
    if request.method == "GET":
        if Socorro.objects.all().exists():
            socorro = Socorro.objects.get(id=id)
            servs_socorro = Servico_Socorro.objects.filter(socorro=id,data_fim__isnull=True )
            mecanicos = Funcionario.objects.filter(funcao='MECANICO')
            print(servs_socorro)
            equipamentos = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
            grupos = Grupo_Servico.objects.all()
            terceirizados = Servico_Terceirizado.objects.all()
            return render(request, 'socorro.html', {'servicos_socorro': servs_socorro,
                                                    'socorro':socorro,
                                                    'id_Socorro':id,
                                                    'equipamentos':equipamentos,
                                                    'grupos':grupos,
                                                    'mecanicos':mecanicos,
                                                    'terceirizados':terceirizados})

        else:
            return redirect('/manutencao/home_manutencao/')
    
    elif request.method == 'POST':
        form_abrir_servico = request.POST.get('form_abrir_servico')
        form_fim_socorro = request.POST.get('form_fim_socorro')
        form_servico_socorro = request.POST.get('form_servico_socorro')

        if form_abrir_servico:
            socorro = Socorro.objects.get(id=id)
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            grupo_id = request.POST.get('grupo_servico')
            grupo = Grupo_Servico.objects.get(id=grupo_id)
            mecanico_id = request.POST.get('mecanico')
            mecanico = Funcionario.objects.get(id=mecanico_id)
            descricao = request.POST.get('descricao')

            if Servico_Socorro.objects.aggregate(Max('numero'))['numero__max'] == None:
                numero = 0
            else:
                numero = Ordem_Oficina.objects.aggregate(Max('numero'))['numero__max']

            servico_socorro = Servico_Socorro(socorro =socorro,
                                              equipamento=equipamento,
                                              grupo_servico=grupo,
                                              mecanico=mecanico,
                                              descricao=descricao,
                                              numero=numero+1)
            
            servico_socorro.save()
            return redirect(f'/manutencao/socorro/{id}/')

        elif form_servico_socorro:
            id_servico_socorro = request.POST.get('id_servico_socorro')
            servico_socorro = Servico_Socorro.objects.get(id=id_servico_socorro)
            mecanico_id = request.POST.get('mecanico')
            print(mecanico_id)

            if mecanico_id == 'None':
                pass
            else: 
                mecanico = Funcionario.objects.get(id=mecanico_id)
                servico_socorro.mecanico = mecanico
            descricao = request.POST.get('descricao')
            servico_socorro.descricao += "-" +  descricao


            data_inicio = request.POST.get('data_inicio')
            data_fim = request.POST.get('data_fim')
            print(data_fim,data_fim)
            if data_inicio == "" or data_fim ==  "":
                pass
            else:

                data_inicio = datetime.strptime(data_inicio, "%Y-%m-%dT%H:%M")    
                servico_socorro.data_inicio = data_inicio
                data_fim = datetime.strptime(data_fim, "%Y-%m-%dT%H:%M")    
                servico_socorro.data_fim = data_fim
                tempo_servico = (data_fim.timestamp() - data_inicio.timestamp())/3600
                servico_socorro.tempo_servico = tempo_servico
            resultado_servico = request.POST.get('resultado_servico')
            if resultado_servico == 'on':
                resultado_servico = True
            else:
                resultado_servico = False
            servico_socorro.resultado_servico = resultado_servico

            ##Criação de objeto registro de mecanico - tempo serviço

            registro_servico = Registro_Tempo_Servico(servico_socorro=servico_socorro,
                                                      funcionario=mecanico,
                                                      data_inicial=data_inicio,
                                                      data_final=data_fim,
                                                      tempo_servico=tempo_servico,
                                                      descricao=descricao)
            registro_servico.save()



            servico_socorro.save()
            return redirect(f'/manutencao/socorro/{id}/')
        
        elif form_fim_socorro:
            socorro = Socorro.objects.get(id=id)
            data_saida = datetime.strptime(socorro.data_saida, "%Y-%m-%dT%H:%M")
            data_chegada = request.POST.get('data_chegada')
            data_chegada = datetime.strptime(data_chegada, "%Y-%m-%dT%H:%M")  
            socorro.data_chegada = data_chegada
            socorro.tempo_socorro = (data_chegada - data_saida)/3600
            socorro.save()

            return redirect('/manutencao/home_manutencao/')

def preventiva(request, id):

    if request.method == 'GET':
        preventiva = Preventiva.objects.get(id=id)
        mecanicos = Funcionario.objects.filter(funcao='MECANICO')

        return render(request, 'preventiva.html', {'preventiva':preventiva,
                                                   'mecanicos':mecanicos,
                                                    'id_Preventiva':id })
    elif request.method == 'POST':

        form_atualizar_preventiva = request.POST.get('form_atualizar_preventiva')
        if form_atualizar_preventiva:
            preventiva_atualizada = Preventiva.objects.get(id=id)
            
            mecanico_id = request.POST.get('mecanico')
            if mecanico_id == 'None':
                pass
            else:
                mecanico = Funcionario.objects.get(id=mecanico_id)
                preventiva_atualizada.mecanico = mecanico
            
            data_insumo = request.POST.get('data_insumo')
            if data_insumo == "":
                pass
            else:
                preventiva_atualizada.data_insumo = data_insumo
            
            data_inicio = request.POST.get('data_inicio')
            if data_inicio == "":
                pass
            else:
                data_inicio = datetime.strptime(data_inicio, "%Y-%m-%dT%H:%M")  
                preventiva_atualizada.data_inicio = data_inicio

            data_fim = request.POST.get('data_fim')
            if data_fim == "":
                pass
            else:
                data_fim = datetime.strptime(data_fim, "%Y-%m-%dT%H:%M")
                preventiva_atualizada.data_fim = data_fim
                
            horimetro = request.POST.get('horimetro')
            if horimetro == "":
                pass
            else:
                horimentro = int(horimetro)
                preventiva_atualizada.horimetro = horimetro

            assinatura_responsavel = request.POST.get('assinatura_responsavel')
            if assinatura_responsavel == "on":
                assinatura_responsavel = True
            else:
                assinatura_responsavel = False
            preventiva_atualizada.assinatura_responsavel = assinatura_responsavel
            tempo_servico = (data_fim.timestamp() - data_inicio.timestamp())/3600
            preventiva_atualizada.tempo_servico = tempo_servico
            print((data_fim.timestamp() - data_inicio.timestamp())/3600)

            print(mecanico_id,data_insumo,data_inicio,data_fim, assinatura_responsavel, horimetro, id, "aaaaaaaaaaaaaaaaaaaaaaaa")

            preventiva_atualizada.save()


            ##Criação de objeto registro de mecanico - tempo serviço

            registro_servico = Registro_Tempo_Servico(servico_preventiva = preventiva_atualizada,
                                                      funcionario=mecanico,
                                                      data_inicial=data_inicio,
                                                      data_final=data_fim,
                                                      tempo_servico=tempo_servico,
                                                      descricao = "Preventiva realizada")
            registro_servico.save()

            

            return redirect(f'/manutencao/preventiva/{id}/')

def analise_mecanicos(request):
    #AQUISIÇÃO DAS DATAS NO FORM
    if request.method == 'GET':
        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=7)
    elif request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        if data_inicio == "":
            data_inicio = date.today()
        else:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()

        data_fim = request.POST.get('data_fim')
        if data_fim == "":
            data_fim = date.today()
        else:

            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
    periodo_dias = round((data_fim - data_inicio).total_seconds()/(2.66666666667*3600)) + 9
    print(periodo_dias)

    dias_semanais = 0
    for i in range((data_fim - data_inicio).days + 1):
        data_atual = data_inicio + timedelta(days=i)
        if data_atual.weekday() == 5 or data_atual.weekday() == 6:
            pass
        else:
            dias_semanais += 1
    horas_disponíveis = dias_semanais*9

    #AQUISIÇÃO DE DADOS FROM THE MODEL REGISTRO_SERVICOS, FUNCIONARIO
    mecanicos = Funcionario.objects.filter(funcao="MECANICO")
    nome_mecanico = 'GERÔNIMO'
    mecanico_id = Funcionario.objects.get(nome=nome_mecanico).id
    servicos_mecanico = Servico_Oficina.objects.filter(executante_funcionario=mecanico_id)
    tempos_mecanicos = []
    qtd_servicos = []
    servicos_mecanico = []
    porcent_servico = []
    for mecanico in mecanicos:
        registros_servicos = Registro_Tempo_Servico.objects.filter(funcionario = mecanico.id).filter(data_inicial__date__gte=data_inicio).filter(data_final__date__lte=data_fim)
        tempos_mecanicos.append(registros_servicos.aggregate(Sum('tempo_servico'))['tempo_servico__sum'])
        qtd_servicos.append(registros_servicos.count())
        servicos_mecanico.append(registros_servicos)

    print(servicos_mecanico)
    print(qtd_servicos)
    print(tempos_mecanicos)
    print(data_fim, data_inicio)

    #AGREGANDO LISTAS PARA O FOR DO HTML
    doc_zip = zip(mecanicos, servicos_mecanico, qtd_servicos, tempos_mecanicos)     
    return render(request, 'analise_mecanicos.html', {'doc_zip': doc_zip})

