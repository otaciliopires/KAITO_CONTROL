from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Abastecimento, Tanque, Transferencia, Entrada, Saldo
from ativos.models import Equipamentos, Obras
from autenticacao.models import Usuario
import datetime
from datetime import date, datetime
import calendar
from django.db.models import Sum, Avg, Max
from . utils import nonetest, grafico_vunit
import openpyxl
import json
from operator import itemgetter
from django.contrib import messages
from django.contrib.messages import constants
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db import transaction



""" Para filtrar uma ForeignKey foi necessário adquirir o valor.id do respectivo item. O filtro da ForeignKey requisita que você
faça isso. No value do formulário foi pedido o equipamento.id e a obra.id  --  em seguida, foi utilizado o 
filter(carateristica_objeto__in=lista_variável -- Em que a lista variável é uma lista de id que quer filtrar da ForeignKey"""


@login_required(login_url='/auth/login/')
def home(request):
    
    if request.method == 'GET' and request.user.status=='c':

        
        user = request.user
        obra_user=Obras.objects.filter(usuario=user.id)
        tanques = Tanque.objects.all()
        obras = Obras.objects.all()
        equipamentos = Equipamentos.objects.all()
        print(user)


        #Método para atualizar saldo dos tanques e lançar valores no frontend
        for tanque in tanques:
            if tanque.tipo == "F":
                tanque.estoque = nonetest(Entrada.objects.filter(tanque=tanque).aggregate(Sum('quantidade'))['quantidade__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum']) - nonetest(Transferencia.objects.filter(fixo=tanque).aggregate(Sum('litros'))['litros__sum'])
            if tanque.tipo == 'M':
                tanque.estoque = nonetest(Transferencia.objects.filter(movel=tanque).aggregate(Sum('litros'))['litros__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum'])
            
            tanque.save()
            if tanque.prefixo == 'TC-01':
                tc01 = [tanque.estoque, round(100*tanque.estoque/15000),1]
                
            elif tanque.prefixo == 'TC-02':
                tc02 = [tanque.estoque, round(100*tanque.estoque/30000, 1)]
            elif tanque.prefixo == 'CA-01.1':
                ca01 = [tanque.estoque, round(100*tanque.estoque/4200,1)]
            elif tanque.prefixo == 'CA-02.1':
                ca02 = [tanque.estoque, round(100*tanque.estoque/4500,2)]
        estoque_total = tc01[0]+tc02[0]+ca01[0]+ca02[0]
        porcent_estoque = int(round(100*(estoque_total/(15000+30000+4200+4500)),1))


        #Alterações horímetro equipamento

        tc_total = tc01[0]+tc02[0]
        for equipamento in equipamentos:

            equipamento.save()

        #criação de gráfico semanal no frontend
        form_data = request.GET.get('mes')
        ano = datetime.today().year
        mes = datetime.today().month
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

        mes_atual = request.GET.get('month')

        if mes_atual == None:
            mes_atual = meses[mes-1]
        else:
            mes = meses.index(mes_atual)+1

            

       

        data_inicio_1 = datetime(ano,mes,1)
        data_fim_1 = datetime(ano, mes, 8)
        data_inicio_2 = datetime(ano,mes,9)
        data_fim_2 = datetime(ano, mes, 16)
        data_inicio_3 = datetime(ano,mes,17)
        data_fim_3 = datetime(ano, mes, 24)
        data_inicio_4 = datetime(ano,mes,25)
        if mes == 1 or mes == 3 or mes == 5 or mes == 7 or mes == 8 or mes == 10 or mes == 12:
            data_fim_4 = datetime(ano, mes, 31)
        elif mes == 4 or mes == 6 or mes == 9 or mes == 11:
            data_fim_4 = datetime(ano, mes, 30)
        else:
            data_fim_4 = datetime(ano, mes, 28)



        entradas_1 = Entrada.objects.filter(data_entrega__range=[data_inicio_1, data_fim_1]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas_2 = Entrada.objects.filter(data_entrega__range=[data_inicio_2, data_fim_2]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas_3 = Entrada.objects.filter(data_entrega__range=[data_inicio_3, data_fim_3]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas_4 = Entrada.objects.filter(data_entrega__range=[data_inicio_4, data_fim_4]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas = json.dumps([entradas_1, entradas_2, entradas_3, entradas_4])

        saidas_1 = Abastecimento.objects.filter(data__range=[data_inicio_1, data_fim_1]).aggregate(Sum('litros'))['litros__sum']
        saidas_2 = Abastecimento.objects.filter(data__range=[data_inicio_2, data_fim_2]).aggregate(Sum('litros'))['litros__sum']
        saidas_3 = Abastecimento.objects.filter(data__range=[data_inicio_3, data_fim_3]).aggregate(Sum('litros'))['litros__sum']
        saidas_4 = Abastecimento.objects.filter(data__range=[data_inicio_4, data_fim_4]).aggregate(Sum('litros'))['litros__sum']
        saidas = json.dumps([saidas_1, saidas_2, saidas_3, saidas_4])

        #criação de gráfico de consumo diário e saldo final do dia no frontend
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        dias_grafico = list(range(1, dias_no_mes + 1))
        primeiro_dia_mes = date(ano, mes, 1)

        saldo_acumulado = nonetest(Entrada.objects.filter(data_entrega__lt=primeiro_dia_mes).aggregate(Sum('quantidade'))['quantidade__sum']) - nonetest(Abastecimento.objects.filter(data__lt=primeiro_dia_mes).aggregate(Sum('litros'))['litros__sum'])

        consumo_diario_valores = []
        saldo_diario_valores = []
        for dia in dias_grafico:
            data_dia = date(ano, mes, dia)
            consumo_dia = nonetest(Abastecimento.objects.filter(data=data_dia).aggregate(Sum('litros'))['litros__sum'])
            entrada_dia = nonetest(Entrada.objects.filter(data_entrega=data_dia).aggregate(Sum('quantidade'))['quantidade__sum'])
            saldo_acumulado = saldo_acumulado + entrada_dia - consumo_dia
            consumo_diario_valores.append(consumo_dia)
            saldo_diario_valores.append(saldo_acumulado)

        dias_grafico = json.dumps(dias_grafico)
        consumo_diario = json.dumps(consumo_diario_valores)
        saldo_diario = json.dumps(saldo_diario_valores)


        lista_obras = []
        lista_consumo = []
        lista_entradas = []
        lista_final = []
        print(entradas, saidas, "!!!!!!!!!!!!!!!!!!")
        
        #criação de tabela e grafico de consumo e entardas
        for obra in obras:
            consumo_mensal_obras = Abastecimento.objects.filter(data__month=mes).filter(data__year=ano).filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
            entrada_mensal_obras = Entrada.objects.filter(data_entrega__month=mes).filter(data_entrega__year=ano).filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum']
            lista_obras.append(obra.nome)
            if consumo_mensal_obras == None:
                consumo_mensal_obras = 0
                pass
            else:
                lista_consumo.append(consumo_mensal_obras)

            if entrada_mensal_obras == None:
                entrada_mensal_obras = 0
                pass
                lista_entradas.append(entrada_mensal_obras)
            if entrada_mensal_obras ==0 and consumo_mensal_obras ==0:
                pass
            else:
                lista_final.append([obra, consumo_mensal_obras, entrada_mensal_obras])

        def terceiro_item(list):
                return list[1]

        lista_final = sorted(lista_final, key=terceiro_item)
        # TABELA ENTRADAS E SAÍDAS OBRAS
        sort_obras = lista_final
        # sort_dict_obras = dict(sorted(sort_obras.items(), key=itemgetter(1), reverse=True))
        print(sort_obras)




        
        list_obras=(lista_obras)
        list_consumo = json.dumps(lista_consumo)

        equipamentos = Equipamentos.objects.all()
        list_equip = []
        saidas_equip = []
        for equipamento in equipamentos:
            list_equip.append(equipamento.prefixo)
            saida_equip = Abastecimento.objects.filter(data__month=mes).filter(data__year=ano).filter(equipamento=equipamento).aggregate(Sum('litros'))['litros__sum']
            if saida_equip == None:
                saida_equip = 0
            saidas_equip.append(saida_equip)

            
        #LISTA EQUIPAMENTOS MAIOR CONSUMO
        dict_equip = dict(zip(list_equip,saidas_equip))
        sort_dict = dict(sorted(dict_equip.items(), key=itemgetter(1), reverse=True))
        sort_d = dict(list(sort_dict.items())[:5])
        print(dict_equip)

        #DATA ATUAL
        data_ultimo_abastecimento = Abastecimento.objects.aggregate(ultima_data=Max('data'))['ultima_data']

        # Gerar gráfico com JChart
        entradas_graph = [i[2] for i in lista_final]
        saidas_graph = [i[1] for i in lista_final]
        obras_grafico = [i[0].nome for i in lista_final]

        print(entradas_graph, saidas_graph, obras_grafico)
        



        return render(request, 'home.html', {'tanques':tanques, 
                                             'obras': obras, 
                                             'meses':meses,
                                             'equipamentos':equipamentos, 
                                             'user':user, 
                                            #  'obra_user':obra_user[0], 
                                             'tc01':tc01,
                                             'tc02':tc02,
                                             'tc_total':tc_total,
                                             'ca01':ca01,
                                             'ca02':ca02,
                                             'estoque_total':estoque_total,
                                             'porcent_estoque':porcent_estoque,
                                             'mes_atual':mes_atual,
                                             'entradas':entradas,
                                             'saidas':saidas,
                                             'list_obras':list_obras,
                                             'list_consumo':list_consumo,
                                             'sort_dict':sort_d,
                                             'data_ultimo_abastecimento':data_ultimo_abastecimento,
                                             'sort_obras':sort_obras,
                                             'entradas_graph':entradas_graph,
                                             'saidas_graph':saidas_graph,
                                             'obras_grafico':obras_grafico,
                                             'dias_grafico':dias_grafico,
                                             'consumo_diario':consumo_diario,
                                             'saldo_diario':saldo_diario
                                             })
    
    if request.method == 'POST':

        form_transferencias = request.POST.get('form_transferencias')
        form_entradas = request.POST.get('form_entradas')
        form_test = request.POST.get('form_test')
        form_data = request.POST.get('form_data')
        form_saidas = request.POST.get('form_saidas')

# método acima é para quando for necessário selecionar um form específico em um html com mais de um form
        print(form_saidas)

        if form_saidas:

            tanque_id = request.POST.get('tanque_id')
            tanque = Tanque.objects.get(id=tanque_id)
            obra_id = request.POST.get('obra') #Método para buscar o id de uma ForeignKey
            obra = Obras.objects.get(id=obra_id)
            equipamento_id = request.POST.get('equipamento')
            equipamento =Equipamentos.objects.get(id=equipamento_id)
            
            contador_inicial = request.POST.get('contador_inicial')
            contador_final = request.POST.get('contador_final')
            litros = request.POST.get('saida_litros')
            horimetro = request.POST.get('horimetro')
            operador = request.POST.get('operador')
            data = request.POST.get('data')
            num_saida = Abastecimento.objects.aggregate(Max('numero'))
            num_saida = (num_saida['numero__max'] + 1)

            print('deu certo')

            #lançamento abastecimentos:
            abastecimento = Abastecimento(litros=litros,
                                          contador_inicio=contador_inicial,
                                          contador_fim=contador_final,
                                          horimetro=horimetro,
                                          data=data,
                                          tanque=tanque,
                                          obra=obra,
                                          equipamento=equipamento,
                                          operador=operador,
                                          colaborador= request.user,
                                          numero=num_saida)
            try:
                abastecimento.save()
                print('deu certo')

                messages.add_message(request, constants.SUCCESS, "Abastecimento laçado com sucesso!" )
                return redirect("/ceq/home")
            except:
                print('deu errado')
                messages.add_message(request, constants.ERROR, "ERRO AO LANÇAR O ABASTECIMENTO" )
                return redirect("/ceq/home")




            print(f"{tanque}, {obra}, {equipamento}, {contador_inicial}, {contador_final}, {type(litros)},{horimetro}, {operador}")
            return HttpResponse(f"{data}, {equipamento}, {contador_inicial}, {contador_final}, {litros},{horimetro}, {operador} -- ,tanque:{tanque}  tanque.saldo: {tanque.estoque} -- obra:{obra}, saldo:{obra.saldo}")
        
        
        if form_entradas:

            tanque_id = request.POST.get('tanque_id')
            tanque = Tanque.objects.get(id=tanque_id)
            obra_id = request.POST.get('obra_id')
            obra = Obras.objects.get(id=obra_id)
            data_emissao = request.POST.get('data_nf')
            data_entrega = request.POST.get('data_entrega')
            fornecedor = request.POST.get('fornecedor')
            nota_fiscal = request.POST.get('NF')
            valor_litro = request.POST.get('valor_litro')
            quantidade_litros = request.POST.get('quantidade')
            valor_total = float(valor_litro) * int(quantidade_litros)
            num_entrada = Entrada.objects.aggregate(Max('numero'))
            num_entrada = num_entrada['numero__max']+1

            print('deucerto')

            #lançamento entradas:
            entrada = Entrada(tanque=tanque,
                              nota_fiscal=nota_fiscal,
                              fornecedor=fornecedor,
                              data_nf=data_emissao,
                              data_entrega=data_entrega,
                              obra=obra,
                              quantidade=quantidade_litros,
                              preco_unitario=valor_litro,
                              preco_total=valor_total,
                              colaborador=request.user,
                              numero=num_entrada
                              )
            entrada.save()

            #Método para atualizar saldo dos tanques.
            total_entradas = nonetest(Entrada.objects.filter(tanque=tanque).aggregate(Sum('quantidade'))['quantidade__sum'])
            total_saidas = nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum'])
            total_transferências = nonetest(Transferencia.objects.filter(fixo=tanque).aggregate(Sum('litros'))['litros__sum'])
            tanque.estoque = total_entradas - total_saidas - total_transferências
            tanque.save()
            
            #Método para atualizar saldo da obra.
            total_entradas = nonetest(Entrada.objects.filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum'])
            total_saidas = nonetest(Abastecimento.objects.filter(obra=obra).aggregate(Sum('litros'))['litros__sum'])
            obra.saldo = total_entradas - total_saidas
            obra.save()
            print(f"obra:{obra} ---saldo_obra = {obra.saldo} --- estoque_tanque = {tanque.estoque}")
            return HttpResponse(f"{tanque}, {obra_id}, {type(data_emissao)}, {type(data_entrega)}, {fornecedor}, {nota_fiscal},{valor_litro}, {quantidade_litros}")

        
        if form_transferencias:
            tanque_fixo_id = request.POST.get('tanque_fixo_id')
            tanque_fixo = Tanque.objects.get(id=tanque_fixo_id)
            tanque_movel_id = request.POST.get('tanque_movel_id')
            tanque_movel = Tanque.objects.get(id=tanque_movel_id)

            contador_inicial = request.POST.get('contador_inicio')
            contador_final = request.POST.get('contador_fim')
            litros = float(contador_final) - float(contador_inicial)
            contador_comboio = request.POST.get('contador_comboio')
            data = date.today()

            #lançamento transferências:
            transferencia = Transferencia(fixo=tanque_fixo,
                                          movel=tanque_movel,
                                          contador_inicio=float(contador_inicial),
                                          contador_fim=float(contador_final),
                                          litros=litros,
                                          contador_comboio=float(contador_comboio),
                                          colaborador=request.user,
                                          data=date.today())
            
            transferencia.save()
            #Método para atualizar saldo dos tanques.
            tanque_fixo.estoque = nonetest(Entrada.objects.filter(tanque=tanque_fixo).aggregate(Sum('quantidade'))['quantidade__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque_fixo).aggregate(Sum('litros'))['litros__sum']) - nonetest(Transferencia.objects.filter(fixo=tanque_fixo).aggregate(Sum('litros'))['litros__sum'])
            tanque_movel.estoque = nonetest(Transferencia.objects.filter(movel=tanque_movel).aggregate(Sum('litros'))['litros__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque_movel).aggregate(Sum('litros'))['litros__sum'])
                
            
            tanque_fixo.contador = float(contador_final)
            tanque_movel.contador = float(contador_comboio)
            tanque_fixo.save()
            tanque_movel.save()

            print(f"{tanque_fixo.estoque}, {tanque_movel.estoque}")

            return HttpResponse(f"{tanque_fixo}, {tanque_movel}, {type(contador_inicial)}, {contador_final}, {contador_comboio}, LITROS:{litros}")

    else: return HttpResponse('<h1>Acesso negado</h1>')

@login_required(login_url='/auth/login/')
def operacoes(request):

    if request.method == 'GET' and request.user.status=='c':

        
        user = request.user
        obra_user=Obras.objects.filter(usuario=user.id)
        tanques = Tanque.objects.all()
        obras = Obras.objects.all()
        equipamentos = Equipamentos.objects.all()
        print(user)

        """Esse script serve para verificar dentro de um excel todos os equipamentos e cadastrá-los
        Utilizar esse código mas transformando o excel em um dictionary e cadastrando os dados do dict
        assim ficará masis fácil o cadastro dentro do servidor
        realizar uma verificação para se o equipamento já for cadastrado, não cadastrar mais"""
        # delete_all = Entrada.objects.all()
        # delete_all.delete()
        
        #Método para cadastrar os equipamentos

        # excel = "media/fotos/equipamentos2.xlsx"
        # workbooks = openpyxl.load_workbook(excel)
        # equipamentss = workbooks['Equipamentos']
        # total_list_x=[]
        # list_x = []
        # for i in equipamentss.iter_rows(min_row=2,values_only=True):
        #         equip = i[:4]
        #         print(equip)
        #         if equip[0] == None:
        #                 break
        #         else:
        #             total_list_x.append(equip) 
        # for i in total_list_x:
        #     print(i[3]) 

        # lista_equipamentos = [('RE-02 BRASIL LOCAÇÕES', 'RETROESCAVADEIRA', 'BRASIL LOCAÇÕES', 'T'),
        #                         ('RLU-7625', 'CAÇAMBA', 'RAMINHO', 'T'),
        #                         ('MN-01 COSAMPA', 'MOTONIVELADORA', 'COSAMPA', 'T'),
        #                         ('POX-3E32', 'FIAT TORO', 'MAZINHO', 'T'),
        #                         ('KLZ-0C11', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('KAO-4455', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('EH-01 MX CONSTRUÇÕES', 'ESCAVADEIRA HIDRÁULICA', 'MX CONSTRUÇÕES', 'T'),
        #                         ('RE-01 MX CONSTRUÇÕES', 'RETROESCAVADEIRA', 'MX CONSTRUÇÕES', 'T'),
        #                         ('RETRO ANCHIETA', 'RETROESCAVADEIRA', 'ANCHIETA', 'T'),
        #                         ('MIF-0636', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('JJZ-1B82', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('MNB-7C69', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        #                         ('RLS-6B96', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('ROLO LOCADO', 'ROLO COMPACTADOR VIBRATÓRIO', 'LOCADO', 'T'),
        #                         ('NPW-1B68', 'CAMINHÃO MUNCK', 'INTERBLOCK ', 'T'),
        #                         ('POX-3C62', 'CAMINHÃO CARROCERIA 3X4', 'FAZENDA ARIMATE', 'T'),
        #                         ('MEIO FIO', 'MEIO FIO OBRA', None, 'T'),
        #                         ('KXJ-3C40', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        #                         ('BALDE PARA TRATOR', 'RESERVATÓRIO NA FAZENDA', None, 'T'),
        #                         ('WE TRANSPORTES', 'ACERTO WE LOCAÇÕES E OBRA', 'EDGLEY', 'T'),
        #                         ('RLS-8J35', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('PEU-5344', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        #                         ('RESERVATÓRIO PARA TRATOR', 'RESERVATÓRIO PARA TRATOR DE ESTEIRA', None, 'T'),
        #                         ('EH-02 REALMAQ', 'ESCAVADEIRA HIDRÁULICA', 'REALMAQ', 'T'),
        #                         ('NTS-2338', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        #                         ('MOB-3F89', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('MOTONIVELADORA LOCADA', 'MOTONIVELADORA', None, 'T'),
        #                         ('NQG-3442', 'CAMINHÃO CARROCERIA 3X4', None, 'T'),
        #                         ('OHH-4I33', 'FRETE TERCEIRIZADO', None, 'T'),
        #                         ('SERVIÇO SILO', 'SERVIÇO SILO', None, 'T'),
        #                         ('CARVALHO LOCAÇÕES', 'CARVALHO', 'CARVALHO LOCAÇÕES', 'T'),
        #                         ('PC-01 MINERAÇÃO PAULISTA', 'PÁ CARREGADEIRA', 'MINERAÇÃO PAULISTA', 'T')]

        # for i in lista_equipamentos:

        #     cadastro_equipamentoss = Equipamentos(prefixo=i[0],
        #                                             descricao=i[0],
        #                                             tipo=i[3],
        #                                             proprietario=i[2],
        #                                             horímetro=0)

        #     cadastro_equipamentoss.save()

        
        # saidas = Abastecimento.objects.all()
        # for saida in saidas:
        #     saida.observacao = ""
        #     saida.save()

        



        return render(request, 'operacoes.html', {'tanques':tanques, 
                                             'obras': obras, 
                                             'equipamentos':equipamentos, 
                                             'user':user, } )
    

    if request.method == 'POST':

        form_transferencias = request.POST.get('form_transferencias')
        form_entradas = request.POST.get('form_entradas')
        form_test = request.POST.get('form_test')
        form_data = request.POST.get('form_data')
        form_saidas = request.POST.get('form_saidas')

# método acima é para quando for necessário selecionar um form específico em um html com mais de um form
        print(form_saidas)

        if form_saidas:

            tanque_id = request.POST.get('tanque_id')
            tanque = Tanque.objects.get(id=tanque_id)
            obra_id = request.POST.get('obra') #Método para buscar o id de uma ForeignKey
            obra = Obras.objects.get(id=obra_id)
            equipamento_id = request.POST.get('equipamento')
            equipamento =Equipamentos.objects.get(id=equipamento_id)
            
            contador_inicial = request.POST.get('contador_inicial')
            contador_final = request.POST.get('contador_final')
            litros = request.POST.get('saida_litros')
            horimetro = request.POST.get('horimetro')
            operador = request.POST.get('operador')
            data = request.POST.get('data')
            num_saida = Abastecimento.objects.aggregate(Max('numero'))
            num_saida = (num_saida['numero__max'] + 1)

            print('deu certo')

            #lançamento abastecimentos:
            abastecimento = Abastecimento(litros=litros,
                                          contador_inicio=contador_inicial,
                                          contador_fim=contador_final,
                                          horimetro=horimetro,
                                          data=data,
                                          tanque=tanque,
                                          obra=obra,
                                          equipamento=equipamento,
                                          operador=operador,
                                          colaborador= request.user,
                                          numero=num_saida)
            try:
                abastecimento.save()
                print('deu certo')

                messages.add_message(request, constants.SUCCESS, "Abastecimento laçado com sucesso!" )
                return redirect("/ceq/home")
            except:
                print('deu errado')
                messages.add_message(request, constants.ERROR, "ERRO AO LANÇAR O ABASTECIMENTO" )
                return redirect("/ceq/home")




            print(f"{tanque}, {obra}, {equipamento}, {contador_inicial}, {contador_final}, {type(litros)},{horimetro}, {operador}")
            return HttpResponse(f"{data}, {equipamento}, {contador_inicial}, {contador_final}, {litros},{horimetro}, {operador} -- ,tanque:{tanque}  tanque.saldo: {tanque.estoque} -- obra:{obra}, saldo:{obra.saldo}")
        
        
        if form_entradas:

            tanque_id = request.POST.get('tanque_id')
            tanque = Tanque.objects.get(id=tanque_id)
            obra_id = request.POST.get('obra_id')
            obra = Obras.objects.get(id=obra_id)
            data_emissao = request.POST.get('data_nf')
            data_entrega = request.POST.get('data_entrega')
            fornecedor = request.POST.get('fornecedor')
            nota_fiscal = request.POST.get('NF')
            valor_litro = request.POST.get('valor_litro')
            quantidade_litros = request.POST.get('quantidade')
            valor_total = float(valor_litro) * int(quantidade_litros)
            num_entrada = Entrada.objects.aggregate(Max('numero'))
            num_entrada = num_entrada['numero__max']+1

            print('deucerto')

            #lançamento entradas:
            entrada = Entrada(tanque=tanque,
                              nota_fiscal=nota_fiscal,
                              fornecedor=fornecedor,
                              data_nf=data_emissao,
                              data_entrega=data_entrega,
                              obra=obra,
                              quantidade=quantidade_litros,
                              preco_unitario=valor_litro,
                              preco_total=valor_total,
                              colaborador=request.user,
                              numero=num_entrada
                              )
            entrada.save()

            #Método para atualizar saldo dos tanques.
            total_entradas = nonetest(Entrada.objects.filter(tanque=tanque).aggregate(Sum('quantidade'))['quantidade__sum'])
            total_saidas = nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum'])
            total_transferências = nonetest(Transferencia.objects.filter(fixo=tanque).aggregate(Sum('litros'))['litros__sum'])
            tanque.estoque = total_entradas - total_saidas - total_transferências
            tanque.save()
            
            #Método para atualizar saldo da obra.
            total_entradas = nonetest(Entrada.objects.filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum'])
            total_saidas = nonetest(Abastecimento.objects.filter(obra=obra).aggregate(Sum('litros'))['litros__sum'])
            obra.saldo = total_entradas - total_saidas
            obra.save()
            print(f"obra:{obra} ---saldo_obra = {obra.saldo} --- estoque_tanque = {tanque.estoque}")
            return HttpResponse(f"{tanque}, {obra_id}, {type(data_emissao)}, {type(data_entrega)}, {fornecedor}, {nota_fiscal},{valor_litro}, {quantidade_litros}")

        
        if form_transferencias:
            tanque_fixo_id = request.POST.get('tanque_fixo_id')
            tanque_fixo = Tanque.objects.get(id=tanque_fixo_id)
            tanque_movel_id = request.POST.get('tanque_movel_id')
            tanque_movel = Tanque.objects.get(id=tanque_movel_id)

            contador_inicial = request.POST.get('contador_inicio')
            contador_final = request.POST.get('contador_fim')
            litros = float(contador_final) - float(contador_inicial)
            contador_comboio = request.POST.get('contador_comboio')
            data = date.today()

            #lançamento transferências:
            transferencia = Transferencia(fixo=tanque_fixo,
                                          movel=tanque_movel,
                                          contador_inicio=float(contador_inicial),
                                          contador_fim=float(contador_final),
                                          litros=litros,
                                          contador_comboio=float(contador_comboio),
                                          colaborador=request.user,
                                          data=date.today())
            
            transferencia.save()
            #Método para atualizar saldo dos tanques.
            tanque_fixo.estoque = nonetest(Entrada.objects.filter(tanque=tanque_fixo).aggregate(Sum('quantidade'))['quantidade__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque_fixo).aggregate(Sum('litros'))['litros__sum']) - nonetest(Transferencia.objects.filter(fixo=tanque_fixo).aggregate(Sum('litros'))['litros__sum'])
            tanque_movel.estoque = nonetest(Transferencia.objects.filter(movel=tanque_movel).aggregate(Sum('litros'))['litros__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque_movel).aggregate(Sum('litros'))['litros__sum'])
                
            
            tanque_fixo.contador = float(contador_final)
            tanque_movel.contador = float(contador_comboio)
            tanque_fixo.save()
            tanque_movel.save()

            print(f"{tanque_fixo.estoque}, {tanque_movel.estoque}")

            return HttpResponse(f"{tanque_fixo}, {tanque_movel}, {type(contador_inicial)}, {contador_final}, {contador_comboio}, LITROS:{litros}")

    else: return HttpResponse('<h1>Acesso negado</h1>')



@login_required(login_url='/auth/login/')
def saidas(request):
 if request.user.status=='c':
        
    obras = Obras.objects.all()
    equipamentos = Equipamentos.objects.all()
    list_equipamentos = []
    list_obras =[]

    for e in equipamentos:list_equipamentos.append(e)
    for o in obras: list_obras.append(o)
    

    data_inicio = request.GET.get('data_inicio')
    if data_inicio == None or data_inicio == '': data_inicio = date(2020,1,1)
    else: data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
    data_fim = request.GET.get('data_fim')
    if data_fim == None or data_fim == '': data_fim = date.today()
    else: data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()


    filtro_obras = request.GET.getlist('obra')
    filtro_equipamento = request.GET.getlist('equipamento')
    
    if request.GET.get('data_inicio') or request.GET.get('data_fim') or request.GET.getlist('equipamento') or request.GET.getlist('obra'):

        if not filtro_equipamento:
            filtro_equipamento = list_equipamentos
        if not filtro_obras:
            filtro_obras= list_obras


        saidas_qs = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).filter(equipamento__in=filtro_equipamento).filter(obra__in=filtro_obras).order_by('numero')
        total_saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).filter(equipamento__in=filtro_equipamento).filter(obra__in=filtro_obras).aggregate(Sum('litros'))['litros__sum']

    else:
        saidas_qs = Abastecimento.objects.all().order_by('-numero')
        total_saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).aggregate(Sum('litros'))['litros__sum']

    paginator = Paginator(saidas_qs, 100)
    saidas = paginator.get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)
    querystring = querystring.urlencode()

    user = request.user
    obra_user=Obras.objects.filter(usuario=user.id)
    print(type(data_fim), data_fim)
    print(type(data_inicio), data_inicio)
    print(type(saidas))


    if not request.GET.getlist('obra'):
        obras_selecionadas = []
    else:
        obras_selecionadas = ",".join(filtro_obras)

    if not request.GET.getlist('equipamento'):
        equipamentos_selecionados=[]
    else:
        equipamentos_selecionados =  ",".join(filtro_equipamento)

    obra_ids_selecionados = request.GET.getlist('obra')
    equipamento_ids_selecionados = request.GET.getlist('equipamento')

    return render(request, 'saidas.html', {'saidas': saidas,
                                           'obras': obras,
                                           'equipamentos':equipamentos,
                                           "user":user,
                                           'total_saidas':total_saidas,
                                           'obras_list':obras_selecionadas,
                                           'equipamentos_list': equipamentos_selecionados,
                                           'obra_ids_selecionados': obra_ids_selecionados,
                                           'equipamento_ids_selecionados': equipamento_ids_selecionados,
                                           'data_inicio_raw': request.GET.get('data_inicio', ''),
                                           'data_fim_raw': request.GET.get('data_fim', ''),
                                           'data_inicio':data_inicio,
                                           'data_fim':data_fim,
                                           'querystring':querystring})
 
 elif request.user.status == 'o': 
    return HttpResponse('acesso negado')

@login_required(login_url='/auth/login/')
def entradas(request):
  if request.user.status=='c':

    obras = Obras.objects.all()
    list_obras =[]

    for o in obras: list_obras.append(o)
    

    data_inicio = request.GET.get('data_inicio')
    if data_inicio == None or data_inicio == '': data_inicio = date(2020,1,1)
    else: data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
    data_fim = request.GET.get('data_fim')
    if data_fim == None or data_fim == '': data_fim = date.today()
    else: data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()


    filtro_obra = request.GET.getlist('obra')
    
    if request.GET.get('data_inicio') or request.GET.get('data_fim') or request.GET.getlist('obra'):

        if not filtro_obra:
            filtro_obra= list_obras


        entradas_qs = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).order_by('numero')
        total_entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).aggregate(Sum('quantidade'))['quantidade__sum']


    else:
        entradas_qs = Entrada.objects.all().order_by('-numero')
        total_entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).aggregate(Sum('quantidade'))['quantidade__sum']

    paginator = Paginator(entradas_qs, 100)
    entradas = paginator.get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)
    querystring = querystring.urlencode()

    if not request.GET.getlist('obra'):
        obras_selecionadas = []
    else:
        obras_selecionadas = ",".join(filtro_obra)


    # print(f"{filtro_obra} and {type(filtro_obra)}")
    # print(f"{data_inicio} and {type(data_inicio)}")
    user = request.user
    obra_user=Obras.objects.filter(usuario=user.id)
    print(data_inicio, data_fim, "!!!!!!!!!!!!!!!!!!!!!")

    return render(request, 'entradas.html', {'entradas':entradas,
                                             'obras': obras,
                                             "user":user,
                                             'total_entradas':total_entradas,
                                             'obras_list':obras_selecionadas,
                                             'data_inicio':data_inicio,
                                             'data_fim': data_fim,
                                             'querystring': querystring})
  else: return HttpResponse("<h1>Acesso negado</h1>")

def transferencias(request):
 if request.user.status == "c":

    transferencias_qs = Transferencia.objects.all().order_by('-data', '-id')
    tanque_fixo = Tanque.objects.filter(tipo='F')
    tanque_movel = Tanque.objects.filter(tipo='M')

    print(tanque_movel)
    data_inicio = request.POST.get('data_inicio')
    data_fim = request.POST.get('data_fim')
    tanque = request.POST.getlist('tanque_fixo')
    comboio = request.POST.getlist('tanque_movel')

    if data_inicio or data_fim or tanque or comboio:
        if not data_inicio:
            data_inicio = date(2022,1,1)
        else:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if not data_fim:
            data_fim = date.today()
        else:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        if not tanque:
            tanque = tanque_fixo
        if not comboio:
            comboio = tanque_movel

        transferencias_qs = Transferencia.objects.filter(movel__in=comboio, fixo__in=tanque, data__range=[data_inicio, data_fim]).order_by('-data', '-id')

    paginator = Paginator(transferencias_qs, 100)
    transferencias = paginator.get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)
    querystring = querystring.urlencode()

    return render(request, 'transferencias.html', {'transferencias': transferencias, 'tanque_fixo':tanque_fixo, 'tanque_movel':tanque_movel, 'querystring': querystring})
 else: return HttpResponse('<h1>Acesso Negado</h1>')


def obras(request):

 if request.user.status == "c":
    obras = Obras.objects.filter(status="S").order_by('saldo')
    obras_medicao = Obras.objects.filter(status='M').order_by('saldo')
    saidas = []
    entradas = []
    saidas_medicao = []

    for obra_medicao in obras_medicao:
        metodo_saida_med = Abastecimento.objects.filter(obra=obra_medicao).aggregate(Sum('litros'))['litros__sum']
        saidas_medicao.append(metodo_saida_med)
    

    ceq_obra = Obras.objects.get(nome='CENTRAL DE EQUIPAMENTOS')
    ceq_obra.saldo = Entrada.objects.filter(obra=ceq_obra.id).aggregate(Sum('quantidade'))['quantidade__sum']
    
    for obra in obras:
        metodo_saidas = Abastecimento.objects.filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
        # print(metodo_saidas, obra)
        metodo_entradas = Entrada.objects.filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum']
        if metodo_saidas == None:
            metodo_saidas = 0
        if metodo_entradas == None:
            metodo_entradas = 0
        
        if obra.nome == 'CENTRAL DE EQUIPAMENTOS':
            ceq_obra.saldo = ceq_obra.saldo - metodo_saidas - sum(saidas_medicao)
            metodo_saidas = metodo_saidas + sum(saidas_medicao)

            ceq_obra.save()
        else:
            obra.saldo = metodo_entradas - metodo_saidas
            obra.save()
        saidas.append(metodo_saidas)
        entradas.append(metodo_entradas)
        print(ceq_obra.saldo,obra.nome)


   
    
    my_list = zip(obras, saidas, entradas)
    metodo_saidas_medicao = zip(obras_medicao, saidas_medicao)
    return render(request, 'obras.html', {'my_list': my_list,
                                          'metodo_saidas_medicao': metodo_saidas_medicao})
 else: return HttpResponse("<h1>Acesso Negado</h1>")

def painel_obras(request):
 if request.user.status == "c":

    saidas = Abastecimento.objects.filter(status=False)

    return render(request, "painel_obras.html", {"saidas":saidas})
 else: return HttpResponse("<h1>Acesso Negado</h1>")


def obras_ano(request):
 if request.user.status == 'c':
    if request.method == "GET":
        year = datetime.today().year
    elif request.method == "POST":
        year = request.POST.get("ano")

    g_vunit = grafico_vunit(year)    

    yearb = int(year)-1
    lista =[]
    obras = Obras.objects.all()
    for obra in obras:
        l=[]
        l.append(obra.nome)
        for n in range(1,13):
            total_saidas = nonetest(Abastecimento.objects.filter(obra=obra).filter(data__year=year).filter(data__month=n).aggregate(Sum('litros'))['litros__sum'])
            total_obra = nonetest(Abastecimento.objects.filter(obra=obra).filter(data__year=year).aggregate(Sum('litros'))['litros__sum'])
            l.append(total_saidas)
        l.append(total_obra)
        lista.append(l)  


    saidas_meses = []
    entradas_meses = []
    entradas_meses_valor = []
    preco_unitario_meses =[]
    valor_saidas_meses =[]
    saldo_meses =[]
    saldo_acumulado_meses =[]
    for m in range(1,13):    
        saidas_mes = nonetest(Abastecimento.objects.filter(data__month=m).filter(data__year=year).aggregate(Sum('litros'))['litros__sum'])
        entradas_mes = nonetest(Entrada.objects.filter(data_entrega__month=m).filter(data_entrega__year=year).aggregate(Sum('quantidade'))['quantidade__sum'])
        entradas_mes_valor = nonetest(Entrada.objects.filter(data_entrega__month=m).filter(data_entrega__year=year).aggregate(Sum('preco_total'))['preco_total__sum'])
        preco_unitario_mes = nonetest(Entrada.objects.filter(data_entrega__month=m).filter(data_entrega__year=year).aggregate(Avg('preco_unitario'))['preco_unitario__avg'])
        
        saidas_meses.append(saidas_mes)
        entradas_meses.append(entradas_mes)
        entradas_meses_valor.append(entradas_mes_valor)
        preco_unitario_meses.append(preco_unitario_mes)
    
    for i in range(0, len(saidas_meses)):
        valor_saidas_meses.append(saidas_meses[i]*preco_unitario_meses[i])
        saldo_meses.append(entradas_meses[i]-saidas_meses[i])
    valor_saidas_ano = sum(valor_saidas_meses)
    saldo_ano =sum(saldo_meses)


    saidas_ano = nonetest(Abastecimento.objects.filter(data__year=year).aggregate(Sum('litros'))['litros__sum'])
    entradas_ano = nonetest(Entrada.objects.filter(data_entrega__year=year).aggregate(Sum('quantidade'))['quantidade__sum'])
    entradas_ano_valor = nonetest(Entrada.objects.filter(data_entrega__year=year).aggregate(Sum('preco_total'))['preco_total__sum'])
    preco_unitario_ano = nonetest(Entrada.objects.filter(data_entrega__year=year).aggregate(Avg('preco_unitario'))['preco_unitario__avg'])
    saldo_ano_anterior = Saldo.objects.get(ano=yearb) #coletar um específico objeto
    saldo_ano_anteriorv = Saldo.objects.filter(ano=yearb).aggregate(Sum('quantidade'))['quantidade__sum']
    saldo_acumulado_ano = float(entradas_ano) - float(saidas_ano) + float(saldo_ano_anteriorv)
   
    count = 0
    for i in saldo_meses:
        
        
        if count == 0:
            saldo_acumulado_meses.append(i + saldo_ano_anteriorv)

        else:
            saldo_acumulado_meses.append(i + saldo_acumulado_meses[count-1])
        count+=1
            
    return render(request, 'obras_ano.html', {'obras':obras, 
                                              'lista':lista, 
                                              'saidas_meses':saidas_meses, 
                                              'saidas_ano':saidas_ano, 
                                              'entradas_meses':entradas_meses, 
                                              'entradas_ano':entradas_ano,
                                              'entradas_meses_valor':entradas_meses_valor,
                                              'entradas_ano_valor':entradas_ano_valor,
                                              'preco_unitario_meses':preco_unitario_meses,
                                              'preco_unitario_ano':preco_unitario_ano,
                                              'valor_saidas_meses':valor_saidas_meses,
                                              'valor_saidas_ano':valor_saidas_ano,
                                              'saldo_meses':saldo_meses,
                                              'saldo_ano':saldo_ano,
                                              'yearb':yearb,
                                              'saldo_ano_anterior':saldo_ano_anterior,
                                              'saldo_acumulado_meses':saldo_acumulado_meses,
                                              'saldo_acumulado_ano':saldo_acumulado_ano,
                                              'grafico_vunit':g_vunit})

 else: return HttpResponse("<h1>Acesso Negado</h1>")
def _numero_ou_texto(valor):
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return valor
    return f"'{valor}'" if valor is not None else "(vazio)"


def _validar_entradas(sheet):
    """Valida a aba ENTRADAS linha a linha. Retorna (linhas_validas, erros)."""
    validas = []
    erros = []
    for linha_num, row in enumerate(sheet.iter_rows(min_row=3, values_only=True), start=3):
        ent = row[:10]
        if ent[0] is None:
            break

        linha_erros = []
        tanque = Tanque.objects.filter(prefixo=ent[0]).first()
        if tanque is None:
            linha_erros.append(f"tanque {_numero_ou_texto(ent[0])} não encontrado")

        obra = Obras.objects.filter(nome=ent[8]).first()
        if obra is None:
            linha_erros.append(f"obra {_numero_ou_texto(ent[8])} não encontrada")

        if not ent[3]:
            linha_erros.append("fornecedor não informado")
        if not ent[4]:
            linha_erros.append("nota fiscal não informada")
        if ent[5] is None:
            linha_erros.append("data da nota fiscal não informada")
        if ent[1] is None:
            linha_erros.append("data de entrega não informada")
        if not isinstance(ent[2], (int, float)):
            linha_erros.append(f"quantidade inválida ({_numero_ou_texto(ent[2])})")
        if not isinstance(ent[6], (int, float)):
            linha_erros.append(f"preço unitário inválido ({_numero_ou_texto(ent[6])})")
        if not isinstance(ent[7], (int, float)):
            linha_erros.append(f"preço total inválido ({_numero_ou_texto(ent[7])})")

        if linha_erros:
            erros.append(f"ENTRADAS, linha {linha_num}: " + "; ".join(linha_erros))
        else:
            validas.append({'tanque': tanque, 'obra': obra, 'dados': ent})

    return validas, erros


def _validar_transferencias(sheet):
    validas = []
    erros = []
    for linha_num, row in enumerate(sheet.iter_rows(min_row=3, values_only=True), start=3):
        tr = row[:7]
        if tr[0] is None:
            break

        linha_erros = []
        tanque_fixo = Tanque.objects.filter(prefixo=tr[0]).first()
        if tanque_fixo is None:
            linha_erros.append(f"tanque fixo {_numero_ou_texto(tr[0])} não encontrado")

        tanque_movel = Tanque.objects.filter(prefixo=tr[1]).first()
        if tanque_movel is None:
            linha_erros.append(f"tanque móvel {_numero_ou_texto(tr[1])} não encontrado")

        if not isinstance(tr[2], (int, float)):
            linha_erros.append(f"contador inicial inválido ({_numero_ou_texto(tr[2])})")
        if not isinstance(tr[3], (int, float)):
            linha_erros.append(f"contador final inválido ({_numero_ou_texto(tr[3])})")
        if isinstance(tr[2], (int, float)) and isinstance(tr[3], (int, float)) and tr[3] < tr[2]:
            linha_erros.append("contador final menor que o contador inicial")
        if tr[5] is None:
            linha_erros.append("data não informada")

        if linha_erros:
            erros.append(f"TRANSFERENCIAS, linha {linha_num}: " + "; ".join(linha_erros))
        else:
            validas.append({'tanque_fixo': tanque_fixo, 'tanque_movel': tanque_movel, 'dados': tr})

    return validas, erros


def _validar_saidas(sheet):
    validas = []
    erros = []
    for linha_num, row in enumerate(sheet.iter_rows(min_row=3, values_only=True), start=3):
        sds = row[:11]
        if sds[0] is None:
            break

        linha_erros = []
        tanque = Tanque.objects.filter(prefixo=sds[0]).first()
        if tanque is None:
            linha_erros.append(f"tanque {_numero_ou_texto(sds[0])} não encontrado")

        obra = Obras.objects.filter(nome=sds[2]).first()
        if obra is None:
            linha_erros.append(f"obra {_numero_ou_texto(sds[2])} não encontrada")

        equipamento = Equipamentos.objects.filter(prefixo=sds[3]).first()
        if equipamento is None:
            linha_erros.append(f"equipamento {_numero_ou_texto(sds[3])} não encontrado")

        if sds[1] is None:
            linha_erros.append("data não informada")
        if not isinstance(sds[4], (int, float)):
            linha_erros.append(f"contador inicial inválido ({_numero_ou_texto(sds[4])})")
        if not isinstance(sds[5], (int, float)):
            linha_erros.append(f"contador final inválido ({_numero_ou_texto(sds[5])})")
        if isinstance(sds[4], (int, float)) and isinstance(sds[5], (int, float)) and sds[5] < sds[4]:
            linha_erros.append("contador final menor que o contador inicial")
        if not sds[9]:
            linha_erros.append("operador não informado")

        if linha_erros:
            erros.append(f"SAIDAS, linha {linha_num}: " + "; ".join(linha_erros))
        else:
            horimetro = sds[7] if isinstance(sds[7], (int, float)) else 0
            lubrificacao = sds[8] is not None
            validas.append({
                'tanque': tanque, 'obra': obra, 'equipamento': equipamento,
                'horimetro': horimetro, 'lubrificacao': lubrificacao, 'dados': sds,
            })

    return validas, erros


def importexcel(request):
    if request.method == 'POST':
        if 'excel' in request.FILES:
            excelfile = request.FILES['excel']
            try:
                workbook = openpyxl.load_workbook(excelfile)
            except Exception:
                messages.add_message(request, constants.ERROR,
                    "Não foi possível ler o arquivo. Verifique se é um .xlsx válido.")
                return redirect('home/')

            abas_esperadas = ['ENTRADAS', 'TRANSFERENCIAS', 'SAIDAS']
            abas_faltando = [a for a in abas_esperadas if a not in workbook.sheetnames]
            if abas_faltando:
                messages.add_message(request, constants.ERROR,
                    f"Planilha inválida: aba(s) não encontrada(s): {', '.join(abas_faltando)}")
                return redirect('home/')

            user_id = request.user

            entradas_validas, erros_entradas = _validar_entradas(workbook['ENTRADAS'])
            transferencias_validas, erros_transferencias = _validar_transferencias(workbook['TRANSFERENCIAS'])
            saidas_validas, erros_saidas = _validar_saidas(workbook['SAIDAS'])

            erros = erros_entradas + erros_transferencias + erros_saidas

            if erros:
                messages.add_message(request, constants.ERROR,
                    f"Importação cancelada: {len(erros)} erro(s) encontrado(s). Nenhum lançamento foi feito. Corrija a planilha e envie novamente.")
                for erro in erros:
                    messages.add_message(request, constants.ERROR, erro)
                return redirect('home/')

            if not entradas_validas and not transferencias_validas and not saidas_validas:
                messages.add_message(request, constants.WARNING, "Nenhum lançamento encontrado na planilha.")
                return redirect('home/')

            with transaction.atomic():
                for item in entradas_validas:
                    ent = item['dados']
                    num_entrada = Entrada.objects.aggregate(Max('numero'))['numero__max']
                    num_entrada = (num_entrada or 0) + 1
                    Entrada.objects.create(
                        tanque=item['tanque'],
                        nota_fiscal=ent[4],
                        fornecedor=ent[3],
                        data_nf=ent[5],
                        data_entrega=ent[1],
                        obra=item['obra'],
                        quantidade=ent[2],
                        preco_unitario=ent[6],
                        preco_total=ent[7],
                        colaborador=user_id,
                        descricao=ent[9] or "",
                        numero=num_entrada,
                    )

                for item in transferencias_validas:
                    tr = item['dados']
                    Transferencia.objects.create(
                        fixo=item['tanque_fixo'],
                        movel=item['tanque_movel'],
                        contador_inicio=tr[2],
                        contador_fim=tr[3],
                        litros=tr[3] - tr[2],
                        contador_comboio=tr[6] or 0,
                        colaborador=user_id,
                        data=tr[5],
                    )

                for item in saidas_validas:
                    sds = item['dados']
                    num_saida = Abastecimento.objects.aggregate(Max('numero'))['numero__max']
                    num_saida = (num_saida or 0) + 1
                    Abastecimento.objects.create(
                        litros=sds[5] - sds[4],
                        contador_inicio=sds[4],
                        contador_fim=sds[5],
                        horimetro=item['horimetro'],
                        data=sds[1],
                        tanque=item['tanque'],
                        obra=item['obra'],
                        equipamento=item['equipamento'],
                        lubrificacao=item['lubrificacao'],
                        operador=sds[9],
                        colaborador=user_id,
                        status=True,
                        observacao=sds[10] or "",
                        numero=num_saida,
                    )

            messages.add_message(request, constants.SUCCESS,
                f"Arquivo importado com sucesso! {len(entradas_validas)} entrada(s), "
                f"{len(transferencias_validas)} transferência(s), {len(saidas_validas)} abastecimento(s) lançados.")
        else:
            messages.add_message(request, constants.ERROR, "Nenhum arquivo enviado.")
    return redirect('home/')



import matplotlib.pyplot as plt
import numpy as np
import base64
from django.core.files.base import ContentFile


def relatorio(request):

      #criação de gráfico semanal no frontend
        form_data = request.GET.get('mes')
        ano = datetime.today().year
        mes = datetime.today().month
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

        mes_atual = request.GET.get('month')

        if mes_atual == None:
            mes_atual = meses[mes-1]
        else:
            mes = meses.index(mes_atual)+1

        if mes_atual == None:
            mes_atual = meses[mes-1]
        else:
            mes = meses.index(mes_atual)+1
        
        lista_obras = []
        lista_consumo = []
        lista_entradas = []
        lista_final = []

        obras = Obras.objects.all()
            #criação de gráfico obras no frontend
        for obra in obras:
            consumo_mensal_obras = Abastecimento.objects.filter(data__month=mes).filter(data__year=ano).filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
            entrada_mensal_obras = Entrada.objects.filter(data_entrega__month=mes).filter(data_entrega__year=ano).filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum']
            lista_obras.append(obra.nome)
            if consumo_mensal_obras == None:
                consumo_mensal_obras = 0
                pass
            else:
                lista_consumo.append(consumo_mensal_obras)

            if entrada_mensal_obras == None:
                entrada_mensal_obras = 0
                pass
                lista_entradas.append(entrada_mensal_obras)
            if entrada_mensal_obras ==0 and consumo_mensal_obras ==0:
                pass
            else:
                lista_final.append([obra, consumo_mensal_obras, entrada_mensal_obras])

        list_obras=(lista_obras)
        list_consumo = json.dumps(lista_consumo)

        def terceiro_item(list):
            return list[1]

        lista_final = sorted(lista_final, key=terceiro_item)
        # TABELA ENTRADAS E SAÍDAS OBRAS
        sort_obras = lista_final
        # sort_dict_obras = dict(sorted(sort_obras.items(), key=itemgetter(1), reverse=True))
        print(sort_obras)



           # Gerar gráfico com Matplotlib
        entradas = [i[2] for i in lista_final]
        saidas = [i[1] for i in lista_final]
        obras_grafico = [i[0].nome for i in lista_final]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ind = np.arange(len(obras_grafico))  # localizações no eixo x
        width = 0.35  # largura das barras
        ax.bar(ind, entradas, width, label='Diesel Recebido', color='blue')
        ax.bar(ind, saidas, width, bottom=entradas, label='Diesel Consumido', color='red')

        ax.set_xlabel('Obras')
        ax.set_ylabel('Quantidade de Diesel')
        ax.set_title(f'Gráfico de Diesel Recebido e Consumido - {mes_atual}')
        ax.set_xticks(ind)
        ax.set_xticklabels(obras_grafico)
        ax.legend()

        # Salvar a imagem do gráfico em base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()

        return render(request, 'relatorio.html', {
            'meses': meses,
            'mes_atual': mes_atual,
            'obras_grafico': obras_grafico,
            'entradas': entradas,
            'saidas': saidas,
            'sort_obras':sort_obras
        })






import json
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
from django.core.files.storage import default_storage



def pdf_relatorio(request, mes_atual):
    
      #criação de gráfico semanal no frontend
    form_data = request.GET.get('mes')
    ano = datetime.today().year
    mes = datetime.today().month
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


    if mes_atual == None:
            mes_atual = meses[mes-1]
    else:
            mes = meses.index(mes_atual)+1

    if mes_atual == None:
            mes_atual = meses[mes-1]
    else:
            mes = meses.index(mes_atual)+1
        
    lista_obras = []
    lista_consumo = []
    lista_entradas = []
    lista_final = []

    obras = Obras.objects.all()
            #criação de gráfico obras no frontend
    for obra in obras:
            consumo_mensal_obras = Abastecimento.objects.filter(data__month=mes).filter(data__year=ano).filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
            entrada_mensal_obras = Entrada.objects.filter(data_entrega__month=mes).filter(data_entrega__year=ano).filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum']
            lista_obras.append(obra.nome)
            if consumo_mensal_obras == None:
                consumo_mensal_obras = 0
                pass
            else:
                lista_consumo.append(consumo_mensal_obras)

            if entrada_mensal_obras == None:
                entrada_mensal_obras = 0
                pass
                lista_entradas.append(entrada_mensal_obras)
            if entrada_mensal_obras ==0 and consumo_mensal_obras ==0:
                pass
            else:
                lista_final.append([obra, consumo_mensal_obras, entrada_mensal_obras])

    list_obras=(lista_obras)
    list_consumo = json.dumps(lista_consumo)

    def terceiro_item(list):
            return list[1]

    lista_final = sorted(lista_final, key=terceiro_item)
        # TABELA ENTRADAS E SAÍDAS OBRAS
    sort_obras = lista_final
        # sort_dict_obras = dict(sorted(sort_obras.items(), key=itemgetter(1), reverse=True))
    print(sort_obras)

               # Gerar gráfico com Matplotlib
    entradas = [i[2] for i in lista_final]
    saidas = [i[1] for i in lista_final]
    obras_grafico = [i[0].nome for i in lista_final]
        
    # Gerar gráfico com Matplotlib
    fig, ax = plt.subplots(figsize=(10, 6))
    ind = np.arange(len(obras_grafico))  # Localizações no eixo x
    width = 0.4  # Largura das barras

    # Criar as barras lado a lado com espaçamento
    ax.bar(ind - width/2 - 0.02, entradas, width=width - 0.02, label='Diesel Recebido', color='blue')  # Ligeiro deslocamento à esquerda
    ax.bar(ind + width/2 + 0.02, saidas, width=width - 0.02, label='Diesel Consumido', color='red')  # Ligeiro deslocamento à direita

    # Ajustar a posição dos ticks do eixo X para ficarem centralizados entre as barras
    ax.set_xticks(ind)  # Ticks permanecem no mesmo índice
    ax.set_xticklabels(obras_grafico, rotation=60, fontsize=8)  # Centralizar os nomes das obras

    # Configurações do gráfico
    ax.set_xlabel('Obras')
    ax.set_ylabel('Quantidade de Diesel')
    ax.set_title(f'Gráfico de Diesel Recebido e Consumido - {mes_atual}')

    # Adicionar legenda
    ax.legend()

    # Ajusta automaticamente o layout para evitar corte de labels
    plt.tight_layout()

    # Salvar a imagem do gráfico em base64
    img_buffer = BytesIO()  # Certifique-se de criar um novo buffer vazio
    plt.savefig(img_buffer, format='png')  # Salva a imagem no buffer
    plt.close(fig)  # Fecha o gráfico
    img_buffer.seek(0)  # Reposiciona o ponteiro no início do buffer

    # Codificando a imagem em base64 para incluir no template HTML
    img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

    # Geração do HTML para o PDF
    html_string = render_to_string('pdf_relatorio.html', {
        'mes_atual': mes_atual,
        'obras_grafico': obras_grafico,
        'entradas': entradas,
        'saidas': saidas,
        'grafico_img': img_base64,
        'sort_obras': lista_final,
    })

    # Geração do PDF usando xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)

    return response

from xhtml2pdf import pisa
def saidas_pdf(request):
    obras = Obras.objects.all()
    equipamentos = Equipamentos.objects.all()
    list_equipamentos = []
    list_obras =[]

    for e in equipamentos:list_equipamentos.append(e)
    for o in obras: list_obras.append(o)
    

    data_inicio = request.GET.get('data_inicio')
    print(data_inicio, "!!!!!!!!!!!!!!!!!!!!!!")
    if data_inicio == None or data_inicio == '': data_inicio = date(2020,1,1)
    else: data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
    data_fim = request.GET.get('data_fim')
    if data_fim == None or data_fim == '': data_fim = date.today()
    else: data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()


    filtro_obras = obras = request.GET.get('obra', '').split(',') if request.GET.get('obra') else []
    filtro_equipamento = request.GET.get('equipamento', '').split(',') if request.GET.get('equipamento') else []
    print(data_inicio, data_fim, "aaaaaaaaaaakcaldmakslmdakndkasnldkakls")
    if request.GET.get('data_inicio') or request.GET.get('data_fim') or request.GET.getlist('equipamento') or request.GET.getlist('obra'):
        if not data_inicio:
            data_inicio = date(2020,1,1)
        if not data_fim:
            data_fim = date.today()
        if filtro_equipamento == ["[]"]:
            filtro_equipamento = list_equipamentos
        if filtro_obras == ["[]"]:
            filtro_obras= list_obras[:100]


        saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).filter(equipamento__in=filtro_equipamento).filter(obra__in=filtro_obras).order_by('numero')
        total_saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).filter(equipamento__in=filtro_equipamento).filter(obra__in=filtro_obras).aggregate(Sum('litros'))['litros__sum']

    else:
        saidas = Abastecimento.objects.all().order_by('-numero')[:100]
        total_saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).aggregate(Sum('litros'))['litros__sum']


    # Renderizar o HTML


    html_index = render_to_string('saidas_pdf.html', {'saidas': saidas, 'total_saidas': total_saidas})
    
    # Criação do PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="documento.pdf"'

    # Converter HTML para PDF
    pisa_status = pisa.CreatePDF(html_index, dest=response)
    
    # Verificar erros
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    
    return response


def entradas_pdf(request):
    obras = Obras.objects.all()

    list_obras = []
    for i in obras: list_obras.append(i)

    #filtro
    data_inicio = request.GET.get('data_inicio1')
    data_fim = request.GET.get('data_fim1')

    filtro_obra = request.GET.getlist('obra')


    print(data_inicio,data_fim, "!!!!!!!!!!!!!!!!!!!!!!!!!!!")



    if data_inicio == None or data_inicio == '': data_inicio = date(2020,1,1)
    else: data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
    if data_fim == None or data_fim == '': data_fim = date.today()
    else: data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

    filtro_obra = obras = request.GET.get('obra', '').split(',') if request.GET.get('obra') else []

    if request.GET.getlist('obra') or request.GET.get('data_inicio') or request.GET.get('data_fim'):

            if filtro_obra == ["[]"]:
                filtro_obra= list_obras
                
            
            entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).order_by('numero')
            total_entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).aggregate(Sum('quantidade'))['quantidade__sum']

        
    else:
            entradas = Entrada.objects.all().order_by('numero')
            total_entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).aggregate(Sum('quantidade'))['quantidade__sum']


    # Renderizar o HTML
    html_index = render_to_string('entradas_pdf.html', {'entradas': entradas, 'total_entradas': total_entradas})
    
    # # Criação do PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="documento.pdf"'

    # # Converter HTML para PDF
    pisa_status = pisa.CreatePDF(html_index, dest=response)
    
    # # Verificar erros
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    
    return response