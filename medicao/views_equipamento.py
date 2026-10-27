"""
Telas da obra para a medição de equipamentos. Isolado do fluxo de caminhão
(medicao_obra_home, medicao_caminhao_lista, medicao_meses, medicao_relatorio
etc. em views.py) — nenhuma função aqui é chamada por, ou chama, aquele
fluxo.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ativos.models import Equipamentos, Obras

from . import calculos_equipamento as calc
from . import servicos_equipamento as servicos
from .models_equipamento import MedicaoEquipamento, MotivoParada, PeriodoMedicaoEquipamento


def _get_obra(request, obra_id):
    obra = get_object_or_404(Obras, id=obra_id)
    if not (request.user.is_superuser or obra.usuario.filter(id=request.user.id).exists()):
        return None, HttpResponse('<h1>Acesso negado</h1>')
    return obra, None


def _get_medicao_da_obra(request, medicao_id):
    medicao = get_object_or_404(
        MedicaoEquipamento.objects.select_related('equipamento', 'obra', 'periodo'), id=medicao_id
    )
    if medicao.obra_id is None:
        # medição aberta direto pela Central, sem obra — não existe pro lado obra
        return None, HttpResponse('<h1>Acesso negado</h1>')
    if not (request.user.is_superuser or medicao.obra.usuario.filter(id=request.user.id).exists()):
        return None, HttpResponse('<h1>Acesso negado</h1>')
    return medicao, None


def _parse_decimal(valor):
    valor = (valor or '').strip().replace(',', '.')
    if not valor:
        return None
    try:
        return Decimal(valor)
    except InvalidOperation:
        raise servicos.ValidacaoDia(f"Valor numérico inválido: {valor}")


@login_required(login_url='/auth/login/')
def medicao_equip_obra_periodos(request, obra_id):
    obra, negado = _get_obra(request, obra_id)
    if negado:
        return negado

    hoje = date.today()
    periodo_atual = servicos.obter_ou_criar_periodo(hoje.year, hoje.month)

    periodos = PeriodoMedicaoEquipamento.objects.order_by('-ano', '-mes')[:12]
    resumo = servicos.resumo_status_por_periodo(obra)

    linhas = []
    for periodo in periodos:
        contagem = resumo.get(periodo.id, {})
        linhas.append({
            'periodo': periodo,
            'total': sum(contagem.values()),
            'rascunho': contagem.get(MedicaoEquipamento.STATUS_RASCUNHO, 0),
            'em_analise': (
                contagem.get(MedicaoEquipamento.STATUS_ENVIADA, 0)
                + contagem.get(MedicaoEquipamento.STATUS_EM_ANALISE, 0)
            ),
            'devolvida': contagem.get(MedicaoEquipamento.STATUS_DEVOLVIDA, 0),
            'fechada': contagem.get(MedicaoEquipamento.STATUS_FECHADA, 0),
        })

    return render(request, 'medicao_equip_obra_periodos.html', {
        'obra': obra, 'linhas': linhas, 'periodo_atual': periodo_atual,
    })


@login_required(login_url='/auth/login/')
def medicao_equip_obra_periodo(request, obra_id, periodo_id):
    obra, negado = _get_obra(request, obra_id)
    if negado:
        return negado

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    medicoes = servicos.medicoes_da_obra(periodo, obra)

    return render(request, 'medicao_equip_obra_periodo.html', {
        'obra': obra, 'periodo': periodo, 'medicoes': medicoes,
    })


@login_required(login_url='/auth/login/')
def medicao_equip_obra_nova_medicao(request, obra_id, periodo_id):
    obra, negado = _get_obra(request, obra_id)
    if negado:
        return negado

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)

    if periodo.status == PeriodoMedicaoEquipamento.STATUS_FECHADO:
        messages.add_message(request, messages.WARNING, 'Esse período já está fechado.')
        return redirect('medicao_equip_obra_periodo', obra_id=obra.id, periodo_id=periodo.id)

    if request.method == 'POST':
        equipamento = get_object_or_404(Equipamentos, id=request.POST.get('equipamento'))
        try:
            medicao = servicos.abrir_medicao(periodo, equipamento, obra, request.user)
        except servicos.AberturaInvalida as erro:
            messages.add_message(request, messages.ERROR, str(erro))
            return redirect('medicao_equip_obra_nova_medicao', obra_id=obra.id, periodo_id=periodo.id)
        return redirect('medicao_equip_obra_medicao', medicao_id=medicao.id)

    equipamentos = servicos.equipamentos_disponiveis_para_medicao(periodo, obra)
    return render(request, 'medicao_equip_obra_nova_medicao.html', {
        'obra': obra, 'periodo': periodo, 'equipamentos': equipamentos,
    })


@login_required(login_url='/auth/login/')
def medicao_equip_obra_medicao(request, medicao_id):
    medicao, negado = _get_medicao_da_obra(request, medicao_id)
    if negado:
        return negado

    consolidado, divergencia = servicos.divergencia_medicao(medicao)
    obras_map = {o.id: o for o in Obras.objects.filter(id__in=consolidado.dias_por_obra.keys())}
    dias_por_obra = [
        {'obra': obras_map.get(obra_id), 'dias': dias}
        for obra_id, dias in consolidado.dias_por_obra.items()
    ]

    if medicao.status == MedicaoEquipamento.STATUS_DEVOLVIDA:
        ajustes = medicao.ajustes_admin.select_related('obra').order_by('obra__nome')
        return render(request, 'medicao_equip_obra_confirmacao.html', {
            'medicao': medicao, 'ajustes': ajustes,
            'consolidado': consolidado, 'divergencia': divergencia, 'dias_por_obra': dias_por_obra,
        })

    apontamentos = medicao.apontamentos.select_related('motivo_parada', 'obra_do_dia').order_by('data')
    motivos = MotivoParada.objects.filter(ativo=True).order_by('descricao')
    todas_obras = Obras.objects.order_by('nome')

    return render(request, 'medicao_equip_obra_grade.html', {
        'medicao': medicao, 'apontamentos': apontamentos, 'motivos': motivos,
        'todas_obras': todas_obras,
        'consolidado': consolidado, 'divergencia': divergencia, 'dias_por_obra': dias_por_obra,
        'editavel': medicao.status == MedicaoEquipamento.STATUS_RASCUNHO,
        'jornada_util': calc.jornada_util_horas(),
    })


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_obra_salvar(request, medicao_id):
    medicao, negado = _get_medicao_da_obra(request, medicao_id)
    if negado:
        return negado

    if medicao.status != MedicaoEquipamento.STATUS_RASCUNHO:
        messages.add_message(request, messages.WARNING, 'Essa medição não pode mais ser editada pela obra.')
        return redirect('medicao_equip_obra_medicao', medicao_id=medicao.id)

    avisos_totais = []
    erros = []

    for apontamento in medicao.apontamentos.order_by('data'):
        prefixo = f'dia_{apontamento.id}_'
        try:
            contador_inicial = _parse_decimal(request.POST.get(prefixo + 'contador_inicial'))
            contador_final = _parse_decimal(request.POST.get(prefixo + 'contador_final'))
            parada = _parse_decimal(request.POST.get(prefixo + 'parada')) or Decimal('0')
            motivo_id = request.POST.get(prefixo + 'motivo') or None
            motivo = MotivoParada.objects.filter(id=motivo_id).first() if motivo_id else None
            obra_dia_id = request.POST.get(prefixo + 'obra_do_dia') or medicao.obra_id
            obra_dia = get_object_or_404(Obras, id=obra_dia_id)
            observacoes = (request.POST.get(prefixo + 'observacoes') or '').strip()

            _, avisos = servicos.salvar_dia(
                apontamento,
                contador_inicial=contador_inicial, contador_final=contador_final,
                parada_horas=parada, motivo=motivo, obra_do_dia=obra_dia, observacoes=observacoes,
            )
            avisos_totais.extend(f"{apontamento.data:%d/%m}: {aviso}" for aviso in avisos)
        except servicos.ValidacaoDia as erro:
            erros.append(f"{apontamento.data:%d/%m}: {erro}")

    if erros:
        messages.add_message(request, messages.ERROR, 'Alguns dias não foram salvos — ' + ' | '.join(erros))
    else:
        messages.add_message(request, messages.SUCCESS, 'Lançamentos salvos.')
    for aviso in avisos_totais:
        messages.add_message(request, messages.WARNING, aviso)

    return redirect('medicao_equip_obra_medicao', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_obra_enviar(request, medicao_id):
    medicao, negado = _get_medicao_da_obra(request, medicao_id)
    if negado:
        return negado

    try:
        servicos.enviar_para_central(medicao, request.user)
        messages.add_message(request, messages.SUCCESS, 'Medição enviada para a Central de Equipamentos.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))

    return redirect('medicao_equip_obra_medicao', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_obra_confirmar(request, medicao_id):
    medicao, negado = _get_medicao_da_obra(request, medicao_id)
    if negado:
        return negado

    try:
        servicos.confirmar_e_fechar(medicao, request.user)
        messages.add_message(request, messages.SUCCESS, 'Medição confirmada e fechada.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))

    return redirect('medicao_equip_obra_periodo', obra_id=medicao.obra_id, periodo_id=medicao.periodo_id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_obra_contestar(request, medicao_id):
    medicao, negado = _get_medicao_da_obra(request, medicao_id)
    if negado:
        return negado

    try:
        servicos.contestar(medicao, request.user, request.POST.get('justificativa', ''))
        messages.add_message(request, messages.INFO, 'Medição contestada — voltou para análise da Central.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))

    return redirect('medicao_equip_obra_medicao', medicao_id=medicao.id)
