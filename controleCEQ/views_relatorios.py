"""Read-only diesel reports, grouped by calendar month and construction site."""
import calendar
import unicodedata
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from ativos.models import Obras
from .models import Abastecimento, Entrada

MESES = ('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro')
ZERO = Decimal('0')


def numero(valor):
    return Decimal(str(valor or 0))


def chave_nome(nome):
    return ''.join(c for c in unicodedata.normalize('NFD', nome) if not unicodedata.combining(c)).casefold()


def semanas_mes(inicio, fim):
    semanas = []
    atual = inicio
    while atual <= fim:
        ultimo = min(atual + timedelta(days=6-atual.weekday()), fim)
        semanas.append({'numero': len(semanas)+1, 'inicio': atual, 'fim': ultimo,
                        'intervalo': atual.strftime('%d/%m')+' – '+ultimo.strftime('%d/%m'),
                        'entradas': ZERO, 'abastecimentos': ZERO, 'registros': 0})
        atual = ultimo + timedelta(days=1)
    return semanas


def comparativo_semanal(entradas, saidas, inicio, fim):
    semanas = semanas_mes(inicio, fim)
    for campo, qs, data_campo, soma_campo in (
        ('entradas', entradas, 'data_entrega', 'quantidade'),
        ('abastecimentos', saidas, 'data', 'litros'),
    ):
        por_dia = qs.values(data_campo).annotate(total=Sum(soma_campo), registros=Count('pk'))
        for linha in por_dia:
            for semana in semanas:
                if semana['inicio'] <= linha[data_campo] <= semana['fim']:
                    semana[campo] += numero(linha['total'])
                    if campo == 'abastecimentos':
                        semana['registros'] += linha['registros']
                    break
    maior = max([s[c] for s in semanas for c in ('entradas', 'abastecimentos')] + [ZERO])
    escala = maior if maior > 0 else Decimal('1')
    passo = 744 / len(semanas)
    largura = min(35, passo * .25)
    for indice, semana in enumerate(semanas):
        semana['resultado'] = semana['entradas'] - semana['abastecimentos']
        semana['centro'] = round(108 + indice * passo + passo / 2, 2)
        for campo, deslocamento in (('entradas', -largura-3), ('abastecimentos', 3)):
            altura = max(0, float(semana[campo] / escala * 166))
            semana[campo+'_barra'] = {
                'x': round(semana['centro'] + deslocamento, 2),
                'y': round(218-altura, 2), 'altura': round(altura, 2),
                'largura': round(largura, 2), 'texto_x': round(semana['centro']+deslocamento+largura/2, 2),
                'texto_y': round(210-altura, 2),
            }
    ticks = [{'y': round(218-166*i/4, 2), 'valor': escala*i/4} for i in range(5)]
    return semanas, ticks


def link_relatorio(periodo, visao, obra_id=None):
    params = {'periodo': periodo, 'visao': visao}
    if obra_id:
        params['obra'] = obra_id
    return '?' + urlencode(params)


def dados_relatorio(request):
    hoje = timezone.localdate()
    aviso = ''
    periodo = request.GET.get('periodo')
    if not periodo and request.GET.get('month') in MESES:
        periodo = '{:04d}-{:02d}'.format(hoje.year, MESES.index(request.GET['month'])+1)
    try:
        inicio = date.fromisoformat((periodo or hoje.strftime('%Y-%m')) + '-01')
        if not 1900 <= inicio.year <= 2100:
            raise ValueError
    except (ValueError, TypeError):
        inicio = hoje.replace(day=1)
        aviso = 'Período inválido. Exibindo o mês atual.'
    fim = inicio.replace(day=calendar.monthrange(inicio.year, inicio.month)[1])
    periodo = inicio.strftime('%Y-%m')
    visao = 'obra' if request.GET.get('visao') == 'obra' else 'mensal'
    obras = sorted(Obras.objects.all(), key=lambda obra: (chave_nome(obra.nome), obra.pk))
    entradas_mes = Entrada.objects.filter(data_entrega__range=(inicio, fim))
    saidas_mes = Abastecimento.objects.filter(data__range=(inicio, fim))
    entradas = {r['obra_id']: r for r in entradas_mes.values('obra_id').annotate(
        total=Sum('quantidade'), valor=Sum('preco_total'), registros=Count('pk'))}
    saidas = {r['obra_id']: r for r in saidas_mes.values('obra_id').annotate(
        total=Sum('litros'), registros=Count('pk'))}
    total_entradas = sum((numero(r['total']) for r in entradas.values()), ZERO)
    total_saidas = sum((numero(r['total']) for r in saidas.values()), ZERO)
    total_valor = sum((numero(r['valor']) for r in entradas.values()), ZERO)
    total_notas = sum(r['registros'] for r in entradas.values())
    total_registros = sum(r['registros'] for r in saidas.values())
    linhas = []
    for obra in obras:
        e, a = entradas.get(obra.pk, {}), saidas.get(obra.pk, {})
        recebido, consumido = numero(e.get('total')), numero(a.get('total'))
        linhas.append({'obra': obra, 'nome': obra.nome, 'entradas': recebido, 'abastecimentos': consumido,
                       'resultado': recebido-consumido, 'registros': a.get('registros', 0),
                       'notas': e.get('registros', 0), 'valor': numero(e.get('valor')),
                       'link': link_relatorio(periodo, 'obra', obra.pk)})
    sem_obra = saidas.get(None, {})
    if sem_obra:
        litros = numero(sem_obra['total'])
        linhas.append({'obra': None, 'nome': 'Sem obra vinculada', 'entradas': ZERO,
                       'abastecimentos': litros, 'resultado': -litros,
                       'registros': sem_obra['registros'], 'notas': 0, 'valor': ZERO})
    obras_movimento = sum(1 for r in linhas if r['obra'] and (r['notas'] or r['registros']))
    selecionada = None
    raw_obra = request.GET.get('obra')
    if raw_obra:
        selecionada = next((obra for obra in obras if str(obra.pk) == raw_obra), None)
        if selecionada is None:
            aviso = 'Obra não encontrada. Selecione uma obra da lista.'
    elif obras:
        maior_consumo = max(linhas, key=lambda r: r['abastecimentos'], default=None)
        selecionada = maior_consumo['obra'] if maior_consumo and maior_consumo['obra'] else obras[0]
    dados_obra = next((r for r in linhas if selecionada and r['obra'] and r['obra'].pk == selecionada.pk), None)
    equipamentos, notas = [], []
    if visao == 'obra':
        entradas_escopo = entradas_mes.filter(obra=selecionada) if selecionada else entradas_mes.none()
        saidas_escopo = saidas_mes.filter(obra=selecionada) if selecionada else saidas_mes.none()
        equipamentos = list(saidas_escopo.values('equipamento_id', 'equipamento__prefixo', 'equipamento__descricao').annotate(
            total=Sum('litros'), registros=Count('pk'), ultimo=Max('data')).order_by('-total', 'equipamento__prefixo', 'equipamento_id'))
        maior_equip = max((numero(e['total']) for e in equipamentos), default=ZERO)
        for equipamento in equipamentos:
            equipamento['total'] = numero(equipamento['total'])
            equipamento['participacao'] = equipamento['total']/dados_obra['abastecimentos']*100 if dados_obra and dados_obra['abastecimentos'] else ZERO
            equipamento['barra'] = round(float(equipamento['total']/maior_equip*100), 2) if maior_equip > 0 else 0
        notas = list(entradas_escopo.order_by('data_entrega', 'pk').values('data_entrega', 'nota_fiscal', 'fornecedor', 'quantidade', 'preco_total'))
    else:
        entradas_escopo, saidas_escopo = entradas_mes, saidas_mes
    semanas, ticks = comparativo_semanal(entradas_escopo, saidas_escopo, inicio, fim)
    ranking = sorted((r for r in linhas if r['abastecimentos'] > 0), key=lambda r: (-r['abastecimentos'], chave_nome(r['nome'])))
    maior_obra = ranking[0]['abastecimentos'] if ranking else ZERO
    for linha in ranking:
        linha['participacao'] = linha['abastecimentos']/total_saidas*100 if total_saidas else ZERO
        linha['barra'] = round(float(linha['abastecimentos']/maior_obra*100), 2) if maior_obra else 0
    resumo = dados_obra if visao == 'obra' else {
        'entradas': total_entradas, 'abastecimentos': total_saidas, 'resultado': total_entradas-total_saidas,
        'registros': total_registros, 'notas': total_notas, 'valor': total_valor,
    }
    if resumo is None:
        resumo = {'entradas': ZERO, 'abastecimentos': ZERO, 'resultado': ZERO, 'valor': ZERO, 'notas': 0, 'registros': 0}
    ultimo_link, ultimo_rotulo = '', ''
    if not total_notas and not total_registros:
        datas = [Entrada.objects.aggregate(d=Max('data_entrega'))['d'], Abastecimento.objects.aggregate(d=Max('data'))['d']]
        ultimo = max((d for d in datas if d), default=None)
        if ultimo and ultimo.strftime('%Y-%m') != periodo:
            ultimo_link = link_relatorio(ultimo.strftime('%Y-%m'), visao, selecionada.pk if selecionada else None)
            ultimo_rotulo = MESES[ultimo.month-1] + ' de ' + str(ultimo.year)
    return {
        'visao': visao, 'periodo': periodo, 'inicio': inicio, 'fim': fim,
        'pdf_link': reverse('relatorio_pdf') + link_relatorio(periodo, visao, selecionada.pk if selecionada else raw_obra),
        'mes_rotulo': MESES[inicio.month-1] + ' de ' + str(inicio.year),
        'mensal_link': link_relatorio(periodo, 'mensal', selecionada.pk if selecionada else None),
        'obra_link': link_relatorio(periodo, 'obra', selecionada.pk if selecionada else None),
        'anterior_link': link_relatorio((inicio-timedelta(days=1)).strftime('%Y-%m'), visao, selecionada.pk if selecionada else None),
        'proximo_link': link_relatorio((fim+timedelta(days=1)).strftime('%Y-%m'), visao, selecionada.pk if selecionada else None),
        'obras': obras, 'obra_selecionada': selecionada, 'resumo': resumo, 'semanas': semanas, 'ticks': ticks,
        'linhas_obras': linhas, 'obras_movimento': obras_movimento, 'ranking_obras': ranking[:6],
        'equipamentos': equipamentos, 'ranking_equipamentos': equipamentos[:6], 'notas': notas,
        'aviso': aviso, 'sem_obra': sem_obra, 'sem_dados': not total_notas and not total_registros,
        'ultimo_link': ultimo_link, 'ultimo_rotulo': ultimo_rotulo, 'gerado_em': timezone.localtime(),
    }


@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def relatorio(request):
    if not (request.user.is_superuser or request.user.status == 'c'):
        return HttpResponseForbidden('Seu usuário não tem acesso aos relatórios gerais de diesel.')
    return render(request, 'relatorio.html', dados_relatorio(request))


@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def relatorio_pdf(request):
    if not (request.user.is_superuser or request.user.status == 'c'):
        return HttpResponseForbidden('Seu usuário não tem acesso aos relatórios gerais de diesel.')
    from .relatorios_pdf import gerar_pdf
    dados = dados_relatorio(request)
    response = HttpResponse(gerar_pdf(dados), content_type='application/pdf')
    tipo = 'mensal' if dados['visao'] == 'mensal' else 'obra'
    response['Content-Disposition'] = 'inline; filename="kaito-relatorio-{}-{}.pdf"'.format(tipo, dados['periodo'])
    return response
