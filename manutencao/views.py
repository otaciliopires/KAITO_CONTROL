from django.shortcuts import render, redirect
from .models import Ordem_Oficina, Servico_Oficina, Grupo_Servico, Funcionario, Servico_Terceirizado, Solicitacao, Socorro, Servico_Socorro, Preventiva, Ordem_Preventiva, Servico_Preventiva, Registro_Tempo_Servico, Pendencias
from .models import Equipamentos, Obras
from datetime import datetime, timezone, date, timedelta
from manutencao.utils import att_tempo_1_os, hora_correta
from django.db.models import Sum, Max


def servicos_manutencao(request):

    if request.method == 'GET':
        equipamentos_rocha = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA').order_by('prefixo')
        obras = Obras.objects.all()
        list_equip = list(equipamentos_rocha)


        #TRATAMENTO  OS CORRETIVAS
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
            else:
                status = "Aguardando Serviço"
                status_serv.append(status)
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
        equipamentos_preventiva= Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA').order_by('prefixo')
        preventivas = Preventiva.objects.filter(data_fim=None)




        return render(request, 'servicos_manutencao.html', {'list_equip':list_equip,
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
            numero = Ordem_Oficina.objects.aggregate(Max('numero'))['numero__max'] or 0

            #adicionar o form da oficina,o de criação de da O.S.
            osoficina = Ordem_Oficina(equipamento=equipamento,
                                        data_inicio=data_inicio,
                                        data_status=data_inicio,
                                        horimetro=horimetro,
                                        numero=numero+1)
            osoficina.save()

            return redirect('/manutencao/servicos_manutencao')
    
        if form_socorro:
            obra_id = request.POST.get('obra')
            obra = Obras.objects.get(id=obra_id) 
            data_saida = request.POST.get('data_saida')
            numero = Socorro.objects.aggregate(Max('numero'))['numero__max'] or 0

            socorro = Socorro(obra = obra,
                              data_saida = data_saida,
                              numero = numero+1,
                              data_chegada = None)

            socorro.save()

            return redirect('/manutencao/servicos_manutencao')
        
        if form_preventiva:
            obra_id = request.POST.get('obra')
            obra = Obras.objects.get(id=obra_id)
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            data_emissao = request.POST.get('data_emissao')
            periodo = int(request.POST.get('periodo'))
            ordem = Ordem_Preventiva.objects.get(equipamento=equipamento, periodo=periodo)
            numero = Preventiva.objects.aggregate(Max('numero'))['numero__max'] or 0

            preventiva = Preventiva(local = obra,
                                    ordem = ordem ,
                                    data_emissao=data_emissao,
                                    numero=numero+1)

            preventiva.save()

            return redirect('/manutencao/servicos_manutencao')


def servico_oficina(request, id):
    if request.method == 'GET':
        if Ordem_Oficina.objects.all().exists():
            ordem_oficina_aberta = Ordem_Oficina.objects.get(id=id)
        else:
            return redirect("/manutencao/servicos_manutencao") 

        servico_oficina = Servico_Oficina.objects.filter(ordem_servico = id).filter(data_fim__isnull=True)

        grupo_servico = Grupo_Servico.objects.all()
        executantes = Funcionario.objects.all()
        terceiros = Servico_Terceirizado.objects.all()

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
            
            numero = Servico_Oficina.objects.aggregate(Max('numero'))['numero__max'] or 0

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
            #colocar a função antes de salvar as informações no BD garante que o valor calculado de tempo seja contabilizado para o status anterior(correto)

            #FECHAR OBJETO DE REGISTRO DE TEMPO DO MECANICO - UTILIZAR SERVICO OFICINA.
            registro_tempo_servico = Registro_Tempo_Servico.objects.get(servico_oficina=servico_oficina.id, data_final=None)
            registro_tempo_servico.data_final = data_status
            registro_tempo_servico.tempo_servico = (data_status.timestamp() - registro_tempo_servico.data_inicial.timestamp())/3600
            registro_tempo_servico.save()

            return redirect(f'/manutencao/osoficina/{id}')

        if form_fim_os:
            data_fim = request.POST.get('data_fim')
            os_oficina = Ordem_Oficina.objects.get(id=id)

            #verificar se tem algum serviço em aberto, caso sim, não salvar a data e fornecer uma mensagem de erro
            os_oficina.data_fim = data_fim
            os_oficina.save()
            return redirect('/manutencao/servicos_manutencao/')
            

def atualizacao_horarios(request):
    now = datetime.now(timezone.utc)
    
    if now.hour - 3 < 7 or now.hour - 3 > 17:
        pass
    else:
        os_oficina_abertas = Ordem_Oficina.objects.filter(data_fim=None)
        for os in os_oficina_abertas:
            att_tempo_1_os(os.id, now)
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




        return redirect('/manutencao/servicos_manutencao/')





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
            if insumo != "":
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
            if solicitacao != "":
                solicitacao_atual.solicitacao = solicitacao

            data_envio = request.POST.get('data_solicitacao')
            if data_envio != "":
                data_envio = datetime.strptime(data_envio, "%Y-%m-%dT%H:%M")
                solicitacao_atual.data_suprimentos = data_envio

            status = request.POST.get('status')
            if status != "Selecionar":
                solicitacao_atual.status = status

            previsao = request.POST.get('data_previsao')
            if previsao != "":
                solicitacao_atual.data_previsao = previsao

            link = request.POST.get('link')
            if link != "":
                solicitacao_atual.link_solicitacao = link

            observacao = request.POST.get('observacao')
            if observacao != "":
                solicitacao_atual.observacao = observacao

            atendida = request.POST.get('atendido')
            if atendida != True:
                atendida = False
            solicitacao_atual.atendida = atendida

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
            return redirect('/manutencao/servicos_manutencao/')
    
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

            socorro.mecanicos.add(mecanico)
            socorro.save()
            return redirect(f'/manutencao/socorro/{id}/')

        elif form_servico_socorro:
            socorro = Socorro.objects.get(id=id)
            id_servico_socorro = request.POST.get('id_servico_socorro')
            servico_socorro = Servico_Socorro.objects.get(id=id_servico_socorro)
            mecanico_id = request.POST.get('mecanico')

            if mecanico_id != 'None':
                mecanico = Funcionario.objects.get(id=mecanico_id)
                servico_socorro.mecanico = mecanico
            descricao = request.POST.get('descricao')
            servico_socorro.descricao += "-" +  descricao

            data_inicio = request.POST.get('data_inicio')
            data_fim = request.POST.get('data_fim')
            if data_inicio != "" and data_fim != "":
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

            socorro.mecanicos.add(mecanico)

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
            data_saida = socorro.data_saida
            data_chegada = request.POST.get('data_chegada')
            data_chegada = datetime.strptime(data_chegada, "%Y-%m-%dT%H:%M")
            data_chegada = data_chegada.replace(tzinfo=None)
            socorro.data_chegada = data_chegada
            socorro.tempo_socorro = (data_chegada.timestamp() - data_saida.timestamp())/3600
            socorro.save()

            return redirect('/manutencao/servicos_manutencao/')

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
            if mecanico_id != 'None':
                mecanico = Funcionario.objects.get(id=mecanico_id)
                preventiva_atualizada.mecanico = mecanico

            data_insumo = request.POST.get('data_insumo')
            if data_insumo != "":
                preventiva_atualizada.data_insumo = data_insumo

            data_inicio = request.POST.get('data_inicio')
            if data_inicio != "":
                data_inicio = datetime.strptime(data_inicio, "%Y-%m-%dT%H:%M")
                preventiva_atualizada.data_inicio = data_inicio

            data_fim = request.POST.get('data_fim')
            if data_fim != "":
                data_fim = datetime.strptime(data_fim, "%Y-%m-%dT%H:%M")
                preventiva_atualizada.data_fim = data_fim

            horimetro = request.POST.get('horimetro')
            if horimetro != "":
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

    dias_semanais = 0
    for i in range((data_fim - data_inicio).days + 1):
        data_atual = data_inicio + timedelta(days=i)
        if data_atual.weekday() != 5 and data_atual.weekday() != 6:
            dias_semanais += 1
    horas_disponíveis = dias_semanais*9

    #AQUISIÇÃO DE DADOS FROM THE MODEL REGISTRO_SERVICOS, FUNCIONARIO
    mecanicos = Funcionario.objects.filter(funcao="MECANICO")
    tempos_mecanicos = []
    qtd_servicos = []
    servicos_mecanico = []
    porcent_servico = []
    tempo_viagens = []
    qtd_viagens = []
    horas_extra=[]
    tempo_ocioso = []
    porcentagens_tempo = []
    
    for mecanico in mecanicos:
        registros_servicos = Registro_Tempo_Servico.objects.filter(funcionario = mecanico.id).filter(data_inicial__date__gte=data_inicio).filter(data_final__date__lte=data_fim)
        soma_tempo_servico_mecanicos = registros_servicos.aggregate(Sum('tempo_servico'))['tempo_servico__sum'] or 0
        tempos_mecanicos.append(soma_tempo_servico_mecanicos) #TEMPO EM SERVIÇOS
        servicos_mecanico.append(registros_servicos)
        qtd_servicos.append(registros_servicos.count())        

        # TEMPO VIAGENS SOCORRO DEBITADO O TEMPO EM SERVIÇO NO SOCORRO
        qtd_socorro = Socorro.objects.filter(data_saida__date__gte=data_inicio).filter(data_chegada__lte=data_fim).filter(mecanicos=mecanico.id).count()
        qtd_viagens.append(qtd_socorro)
        tempo_socorro = Socorro.objects.filter(data_saida__date__gte=data_inicio).filter(data_chegada__date__lte=data_fim).filter(mecanicos=mecanico.id).aggregate(Sum('tempo_socorro'))['tempo_socorro__sum']
        tempo_serv_socorro = Servico_Socorro.objects.filter(data_inicio__date__gte=data_inicio).filter(data_fim__date__lte=data_fim).filter(mecanico=mecanico.id).aggregate(Sum('tempo_servico'))['tempo_servico__sum']
        if tempo_socorro == None:
            tempo_socorro = 0
        if tempo_serv_socorro == None:
            tempo_serv_socorro = 0
        tempo_viagens.append(tempo_socorro - tempo_serv_socorro) #TEMPO EM VIAGENS  - EM SERVIÇOS DE SOCORRO


       #HORAS EXTRAS DE SERVIÇOS E VIAGENS
        current_date = data_inicio
        final_date = data_fim
        tempo_serv_extras = 0
        tempo_viagens_extra = 0
        hora_extra_semana = 0
        total_semana = 0
        while current_date <= final_date:
            if current_date.weekday() != 5 and current_date.weekday() != 6:
                total_semana += 9
                query_tempo_extra_semana = Registro_Tempo_Servico.objects.filter(funcionario__gte=mecanico.id).filter(data_inicial__date__gte=current_date).filter(data_final__date__lte=current_date)

                if query_tempo_extra_semana:
                    for i in query_tempo_extra_semana:
                        i = i.data_final - timedelta(hours=3)
                        i = i.replace(tzinfo=None)
                        if i.hour > 17:

                            hora_extra_semana += (i.timestamp() - datetime(i.year, i.month, i.day, 17,0,0).timestamp())/3600



            if current_date.weekday() == 5 or current_date.weekday() == 6:
        
                tempo_socorro_weekend = Socorro.objects.filter(data_saida__date__gte=current_date).filter(data_chegada__lte=current_date).filter(mecanicos=mecanico.id).aggregate(Sum('tempo_socorro'))['tempo_socorro__sum']
                tempo_serv_socorro_weekend = Registro_Tempo_Servico.objects.filter(funcionario = mecanico.id).filter(data_inicial__date__gte=current_date).filter(data_final__date__lte=current_date).filter(servico_socorro__isnull=False).aggregate(Sum('tempo_servico'))['tempo_servico__sum']
                if tempo_socorro_weekend == None:
                    tempo_socorro_weekend = 0
                if tempo_serv_socorro_weekend == None:
                    tempo_serv_socorro_weekend = 0
                tempo_viagens_extra += (tempo_socorro_weekend - tempo_serv_socorro_weekend)
                
                tempo_serv_extra = Registro_Tempo_Servico.objects.filter(funcionario__gte=mecanico.id).filter(data_inicial__date__gte=current_date).filter(data_final__date__lte=current_date).aggregate(Sum('tempo_servico'))['tempo_servico__sum']
                if tempo_serv_extra == None:
                    tempo_serv_extras += 0
                else:
                    tempo_serv_extras +=tempo_serv_extra

            current_date += timedelta(days=1)
        horas_extra.append(tempo_serv_extras+tempo_viagens_extra+hora_extra_semana)
        tempo_ocioso.append(total_semana - (tempo_socorro - tempo_serv_socorro) - soma_tempo_servico_mecanicos)
        porcentagens_tempo.append([(soma_tempo_servico_mecanicos / total_semana)*100,((tempo_socorro - tempo_serv_socorro)/total_semana)*100, (((total_semana - (tempo_socorro - tempo_serv_socorro) - soma_tempo_servico_mecanicos)/total_semana)*100), ((tempo_serv_extras+tempo_viagens_extra+hora_extra_semana)/total_semana)*100  ])
    #AGREGANDO LISTAS PARA O FOR DO HTML
    doc_zip = zip(mecanicos, servicos_mecanico, qtd_servicos, tempos_mecanicos, tempo_viagens, qtd_viagens, horas_extra, tempo_ocioso, porcentagens_tempo)
    return render(request, 'analise_mecanicos.html', {'doc_zip': doc_zip,
                                                      'total_semana':total_semana})

def servicos_post(request):

    if request.method == "GET":
        equipamentos_rocha = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        tipo_servicos = ['Oficina', 'Socorro', 'Preventiva']
        grupos = Grupo_Servico.objects.all()

        return render(request, 'servicos_post.html', {'equipamentos':equipamentos_rocha,
                                                    'tipo_servicos':tipo_servicos,
                                                    'grupos': grupos})
    elif request.method == "POST":

        form = request.POST.get('form')
        equipamentos_rocha = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
        tipo_servicos = ['Oficina', 'Socorro', 'Preventiva']
        grupos = Grupo_Servico.objects.all()

        #coletando os POSTS
        if form:

            all_equipamentos = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
            all_grupos = Grupo_Servico.objects.all()

            list_equipamentos = []
            list_grupos = []

            for e in all_equipamentos: list_equipamentos.append(e)
            for e in all_grupos: list_grupos.append(e)

            tipo_servico = request.POST.get('tipo')
            equipamento_rocha_id = request.POST.get('equipamento')
            grupo_id = request.POST.get('grupo')

            data_inicial = request.POST.get('data_inicial')
            data_final = request.POST.get('data_final')

            if not equipamento_rocha_id:
                    equipamento_rocha_id = list_equipamentos
            if not grupo_id:
                    grupo_id = list_grupos
            if not data_inicial:
                    data_inicial = date.today() - timedelta(days=7)
            if not data_final:
                    data_final = date.today()

            servicos_oficina = Servico_Oficina.objects.filter(ordem_servico__equipamento__in = equipamento_rocha_id).filter(grupo_servico__in = grupo_id).filter(data_fim__gte=data_inicial).filter(data_fim__lte=data_final)
            servico_socorro = Servico_Socorro.objects.filter(equipamento__in = equipamento_rocha_id).filter(grupo_servico__in = grupo_id).filter(data_inicio__gte = data_inicial).filter(data_fim__lte = data_final)
            preventiva = Preventiva.objects.filter(ordem__equipamento__in = equipamento_rocha_id).filter(data_inicio__gte = data_inicial).filter(data_fim__lte = data_final)

            #adiquirindo lista com as informações de serviços oficina
            serv_oficina_list=[]
            for serv_oficina in servicos_oficina:
                s_o = []
                s_o.append("Oficina")
                s_o.append(serv_oficina.ordem_servico.equipamento.prefixo)
                s_o.append(serv_oficina.grupo_servico.grupo)
                s_o.append(serv_oficina.data_inicio)
                s_o.append(serv_oficina.data_fim)
                s_o.append(serv_oficina.tempo_em_servico)
                s_o.append(serv_oficina.descricao)
                serv_oficina_list.append(s_o)
            for serv_socorro in servico_socorro:
                 s_s = []
                 s_s.append("Socorro")
                 s_s.append(serv_socorro.equipamento)
                 s_s.append(serv_socorro.grupo_servico)
                 s_s.append(serv_socorro.data_inicio)
                 s_s.append(serv_socorro.data_fim)
                 s_s.append(serv_socorro.tempo_servico)
                 s_s.append(serv_socorro.descricao)
                 serv_oficina_list.append(s_s)
            for serv_preventiva in preventiva:
                 p = []
                 p.append("Preventiva")
                 p.append(serv_preventiva.ordem.equipamento)
                 p.append('preventiva')
                 p.append(serv_preventiva.data_inicio)
                 p.append(serv_preventiva.data_fim)
                 p.append(serv_preventiva.tempo_servico)
                 p.append(serv_preventiva.ordem)
                 serv_oficina_list.append(p)


            return render(request, 'servicos_post.html', {'serv_oficina_list':serv_oficina_list,
                                                          'equipamentos':equipamentos_rocha,
                                                          'tipo_servicos':tipo_servicos,
                                                          'grupos': grupos})


def pendencias(request):
    if request.method == 'GET':     

     equipamentos = Equipamentos.objects.filter(proprietario='CONSTRUTORA ROCHA')
     pendencias = Pendencias.objects.filter(data_fim__isnull=True)
     situacoes = ['Parado', 'Trabalhando']
     status = ['Aguardando Peças', 'Aguardando Serviços']

     
     

     return render(request, 'pendencias.html', {'equipamentos':equipamentos,
                                                'situacoes':situacoes,
                                                'status':status,
                                                'pendencias':pendencias})
    if request.method == 'POST':

        form_add_pendencias = request.POST.get('form_add_pendencias')
        form_att_pendencias = request.POST.get('form_att_pendencias')
        
        if form_add_pendencias:
            equipamento_id = request.POST.get('equipamento')
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            data_inicio = request.POST.get('data_inicio')
            descricao = request.POST.get('descricao')
            status = request.POST.get('status')
            situacao = request.POST.get('situacao')

            pendencia = Pendencias(equipamento = equipamento,
                                   status = status,
                                   situacao = situacao,
                                   data_inicio = data_inicio,
                                   descricao = descricao)
            pendencia.save()

        return redirect('/manutencao/pendencias/') 
    
    if form_att_pendencias:
        id_pendencia = request.POST.get('id_pendencia')
        pendencia = Pendencias.objects.get(id=id_pendencia)
        pendencia.status = request.POST.get('status')
        pendencia.situacao = request.POST.get('situacao')
        add_descricao = request.POST.get('descricao')
        pendencia.descricao = pendencia.descricao + add_descricao

        if request.POST.get('data_fim') == "":
            pass
        else:
            pendencia.data_fim = request.POST.get('data_fim')

        pendencia.save()

        return redirect('/manutencao/pendencias/')   
    

def home_manutencao(request):


    return render(request, 'home_manutencao.html')