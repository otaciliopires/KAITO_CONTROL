"""Shared, read-only filters for the outgoing-fuel list, equipment choices and PDF."""
import re
import unicodedata
from datetime import date
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.utils import timezone
from .saidas_pdf import FIELDS, gerar_saidas_pdf

from ativos.models import Equipamentos, Obras
from .colunas_saidas import COLUNAS, selecionar_colunas
from .models import Abastecimento


def chave_nome(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto or '') if not unicodedata.combining(c)).casefold()
    return tuple(int(p) if p.isdigit() else p for p in re.split(r'(\d+)', texto))


def ids_selecionados(params, campo):
    # Repeated parameters are canonical; comma lists remain supported for old PDF links.
    resultado = []
    for valor in params.getlist(campo):
        for parte in valor.split(','):
            parte = parte.strip()
            if parte in ('', '[]'):
                continue
            if not parte.isascii() or not parte.isdigit() or len(parte) > 18 or int(parte) < 1:
                raise ValueError('Selecione obras e equipamentos válidos nas listas.')
            normalizado = str(int(parte))
            if normalizado not in resultado:
                resultado.append(normalizado)
    return resultado


def filtros_primarios(params, aplicar_obras=True):
    inicio_raw, fim_raw = params.get('data_inicio', '').strip(), params.get('data_fim', '').strip()
    try:
        inicio = date.fromisoformat(inicio_raw) if inicio_raw else None
        fim = date.fromisoformat(fim_raw) if fim_raw else None
    except ValueError:
        raise ValueError('Informe datas válidas para o período da consulta.')
    if inicio and fim and inicio > fim:
        raise ValueError('A data inicial deve ser anterior ou igual à data final.')
    obras = ids_selecionados(params, 'obra')
    qs = Abastecimento.objects.all()
    if inicio:
        qs = qs.filter(data__gte=inicio)
    if fim:
        qs = qs.filter(data__lte=fim)
    if obras and aplicar_obras:
        qs = qs.filter(obra_id__in=obras)
    return qs, inicio, fim, obras


def obras_do_periodo(params):
    base, _, _, _ = filtros_primarios(params, aplicar_obras=False)
    return sorted(Obras.objects.filter(pk__in=base.order_by().values('obra_id')),
                  key=lambda o: (chave_nome(o.nome), o.pk))


def equipamentos_do_recorte(qs):
    opcoes = Equipamentos.objects.filter(pk__in=qs.order_by().values('equipamento_id'))
    return sorted(opcoes, key=lambda e: (chave_nome(e.prefixo), e.pk))


def consulta_saidas(params):
    base, inicio, fim, obras = filtros_primarios(params)
    colunas = selecionar_colunas(params)
    equipamentos = ids_selecionados(params, 'equipamento')
    qs = base.filter(equipamento_id__in=equipamentos) if equipamentos else base
    qs = qs.select_related('obra', 'equipamento', 'tanque').order_by('-numero', '-pk')
    pares = []
    if inicio:
        pares.append(('data_inicio', inicio.isoformat()))
    if fim:
        pares.append(('data_fim', fim.isoformat()))
    pares.extend(('obra', item) for item in obras)
    pares.extend(('equipamento', item) for item in equipamentos)
    if 'coluna' in params or params.get('personalizar_colunas') == '1':
        pares.append(('personalizar_colunas','1'))
        pares.extend(('coluna', c['id']) for c in colunas)
    return {'colunas': colunas, 'base': base, 'saidas': qs, 'inicio': inicio, 'fim': fim,
            'obras': obras, 'equipamentos': equipamentos, 'querystring': urlencode(pares)}


def tem_acesso(user):
    return user.is_superuser or user.status == 'c'


@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def saidas(request):
    if not tem_acesso(request.user):
        return HttpResponseForbidden('Seu usuário não tem acesso às saídas de diesel.')
    erro, aviso = '', ''
    try:
        consulta = consulta_saidas(request.GET)
        obras = obras_do_periodo(request.GET)
        equipamentos = equipamentos_do_recorte(consulta['base'])
        if set(consulta['obras']) - {str(o.pk) for o in obras}:
            aviso = 'Há obras aplicadas sem abastecimentos neste período. Elas foram desmarcadas na lista; clique em Filtrar para atualizar a consulta.'
        disponiveis = {str(e.pk) for e in equipamentos}
        if set(consulta['equipamentos']) - disponiveis:
            aviso += ' Há equipamentos aplicados sem abastecimentos neste recorte. Eles foram desmarcados na lista; clique em Filtrar para atualizar a consulta ou selecione outros equipamentos.'
        total = consulta['saidas'].aggregate(total=Sum('litros'))['total'] or 0
    except ValueError as exc:
        erro = str(exc)
        consulta = {'saidas': Abastecimento.objects.none(), 'obras': [], 'equipamentos': [], 'querystring': '', 'inicio': None, 'fim': None}
        obras, equipamentos, total = [], [], 0
    pagina = Paginator(consulta['saidas'], 100).get_page(request.GET.get('page'))
    return render(request, 'saidas.html', {
        'saidas': pagina, 'obras': obras, 'equipamentos': equipamentos, 'total_saidas': total,
        'obra_ids_selecionados': consulta['obras'], 'equipamento_ids_selecionados': consulta['equipamentos'],
        'data_inicio_raw': request.GET.get('data_inicio', ''), 'data_fim_raw': request.GET.get('data_fim', ''),
        'querystring': consulta['querystring'], 'erro_filtro': erro, 'aviso_filtro': aviso,
        'tem_filtros': bool(consulta['inicio'] or consulta['fim'] or consulta['obras'] or consulta['equipamentos']),
        'colunas_disponiveis': COLUNAS,
        'colunas_visiveis': [c['id'] for c in consulta.get('colunas', COLUNAS)],
        'largura_tabela': max(320,min(1250,len(consulta.get('colunas',COLUNAS))*114)),
        'obra_user': Obras.objects.filter(usuario=request.user),
    }, status=400 if erro else 200)


@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def equipamentos_saidas(request):
    if not tem_acesso(request.user):
        return JsonResponse({'erro': 'Seu usuário não tem acesso a esta consulta.'}, status=403)
    try:
        base, _, _, selecionadas = filtros_primarios(request.GET, aplicar_obras=False)
        obras = obras_do_periodo(request.GET)
        validas = set(selecionadas) & {str(o.pk) for o in obras}
        if validas:
            base = base.filter(obra_id__in=validas)
    except ValueError as exc:
        return JsonResponse({'erro': str(exc)}, status=400)
    equipamentos = equipamentos_do_recorte(base)
    return JsonResponse({'obras': [{'id': o.pk, 'nome': o.nome} for o in obras], 'equipamentos': [{'id': e.pk, 'prefixo': e.prefixo, 'descricao': e.descricao or ''} for e in equipamentos]})


@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def saidas_pdf(request):
    if not tem_acesso(request.user):
        return HttpResponseForbidden('Seu usuário não tem acesso às saídas de diesel.')
    try:
        consulta = consulta_saidas(request.GET)
    except ValueError as exc:
        return HttpResponse(str(exc), status=400, content_type='text/plain; charset=utf-8')
    registros = list(consulta['saidas'].values(*FIELDS))
    obras = Obras.objects.filter(pk__in=consulta['obras']).order_by('nome').values_list('nome', flat=True)
    equipamentos = Equipamentos.objects.filter(pk__in=consulta['equipamentos']).order_by('prefixo').values_list('prefixo', flat=True)
    conteudo = gerar_saidas_pdf(registros, consulta, timezone.localtime(), obras, equipamentos)
    response = HttpResponse(conteudo, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="saidas-diesel.pdf"'
    return response
