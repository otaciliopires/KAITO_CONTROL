"""
Telas da Central de Equipamentos (CEQ) para a medição de equipamentos.
Isolado do fluxo de caminhão (medicao_painel_ceq, medicao_fechar_mes etc. em
views.py) — nenhuma função aqui é chamada por, ou chama, aquele fluxo. Também
isolado das telas da obra (views_equipamento.py), exceto pelo compartilhamento
de servicos_equipamento.py e calculos_equipamento.py.
"""
import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ativos.models import Obras

from . import calculos_equipamento as calc
from . import servicos_equipamento as servicos
from .models_equipamento import MedicaoEquipamento, PeriodoMedicaoEquipamento

MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}


def _get_ceq(request):
    if not (request.user.is_superuser or request.user.status == 'c'):
        return HttpResponse('<h1>Acesso negado</h1>')
    return None


def _redirect_painel(periodo):
    return redirect(f"{reverse('medicao_equip_ceq_painel')}?periodo={periodo.ano}-{periodo.mes:02d}")


def _resolver_periodo_da_query(request):
    """Lê ?periodo=AAAA-M da querystring (default: mês atual), garante que o
    PeriodoMedicaoEquipamento existe, e monta as opções do seletor de mês."""
    hoje = date.today()
    try:
        ano_str, mes_str = request.GET.get('periodo', '').split('-')
        ano, mes = int(ano_str), int(mes_str)
        if mes < 1 or mes > 12:
            raise ValueError
    except (ValueError, AttributeError):
        ano, mes = hoje.year, hoje.month

    periodo = servicos.obter_ou_criar_periodo(ano, mes)

    opcoes_mes = []
    ano_it, mes_it = hoje.year, hoje.month
    for _ in range(24):
        opcoes_mes.append({'ano': ano_it, 'mes': mes_it, 'nome': MESES_PT[mes_it]})
        ano_it, mes_it = (ano_it, mes_it - 1) if mes_it > 1 else (ano_it - 1, 12)

    contexto = {
        'periodo': periodo, 'ano_selecionado': ano, 'mes_selecionado': mes,
        'nome_mes_selecionado': MESES_PT[mes], 'opcoes_mes': opcoes_mes,
        'mes_em_andamento': (ano, mes) == (hoje.year, hoje.month),
    }
    return periodo, contexto


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_painel(request):
    negado = _get_ceq(request)
    if negado:
        return negado

    periodo, contexto = _resolver_periodo_da_query(request)
    linhas = [servicos.linha_painel(m) for m in servicos.medicoes_do_periodo(periodo)]
    resumo = servicos.resumo_financeiro(linhas)

    chart_data = {
        'labels': [(l['obra'].nome if l['obra'] else '—') for l in resumo['por_obra']] + ['Manutenção', 'À disposição'],
        'valores': [float(l['valor']) for l in resumo['por_obra']] + [float(resumo['manutencao']), float(resumo['disposicao'])],
    }

    contexto.update({
        'linhas': linhas, 'resumo': resumo,
        'chart_data_json': json.dumps(chart_data),
        'total_pendencias': sum(1 for l in linhas if l['divergencia'] != 0),
    })
    return render(request, 'medicao_equip_ceq_painel.html', contexto)


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_localizacao(request):
    negado = _get_ceq(request)
    if negado:
        return negado

    periodo, contexto = _resolver_periodo_da_query(request)
    obras_colunas, linhas = servicos.matriz_localizacao(periodo)
    contexto.update({'obras_colunas': obras_colunas, 'linhas': linhas})
    return render(request, 'medicao_equip_ceq_localizacao.html', contexto)


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_obra(request, periodo_id, obra_id):
    negado = _get_ceq(request)
    if negado:
        return negado

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    obra = get_object_or_404(Obras, id=obra_id)

    linhas = []
    for medicao in servicos.medicoes_do_periodo(periodo):
        linha = servicos.linha_painel(medicao)
        dias_obra = linha['consolidado'].dias_por_obra.get(obra.id)
        if dias_obra is None:
            continue
        linhas.append({
            'medicao': medicao,
            'dias': dias_obra,
            'fator': calc.calcular_fator_rateio(dias_obra, periodo.dias_do_mes),
            'valor': calc.calcular_valor_rateio(dias_obra, periodo.dias_do_mes, medicao.valor_aluguel_vigente),
        })

    return render(request, 'medicao_equip_ceq_obra.html', {
        'periodo': periodo, 'obra': obra, 'linhas': linhas,
        'total_valor': sum((l['valor'] for l in linhas), Decimal('0.00')),
    })


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_manutencao(request, periodo_id):
    negado = _get_ceq(request)
    if negado:
        return negado

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    linhas = []
    for medicao in servicos.medicoes_do_periodo(periodo):
        linha = servicos.linha_painel(medicao)
        if linha['consolidado'].dias_manutencao <= 0:
            continue
        linhas.append({'medicao': medicao, 'dias': linha['consolidado'].dias_manutencao, 'valor': linha['valor_manutencao']})

    return render(request, 'medicao_equip_ceq_manutencao.html', {
        'periodo': periodo, 'linhas': linhas,
        'total_dias': sum((l['dias'] for l in linhas), Decimal('0.00')),
        'total_valor': sum((l['valor'] for l in linhas), Decimal('0.00')),
    })


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_disposicao(request, periodo_id):
    negado = _get_ceq(request)
    if negado:
        return negado

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    linhas = []
    for medicao in servicos.medicoes_do_periodo(periodo):
        linha = servicos.linha_painel(medicao)
        if linha['consolidado'].dias_disposicao <= 0:
            continue
        linhas.append({'medicao': medicao, 'dias': linha['consolidado'].dias_disposicao, 'valor': linha['valor_disposicao']})

    return render(request, 'medicao_equip_ceq_disposicao.html', {
        'periodo': periodo, 'linhas': linhas,
        'total_dias': sum((l['dias'] for l in linhas), Decimal('0.00')),
        'total_valor': sum((l['valor'] for l in linhas), Decimal('0.00')),
    })


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_nova_medicao_direta(request, periodo_id):
    """Abre uma medição sem obra — equipamento parado (manutenção/à
    disposição) o período inteiro, sem nenhuma obra envolvida."""
    negado = _get_ceq(request)
    if negado:
        return negado

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)

    if periodo.status == PeriodoMedicaoEquipamento.STATUS_FECHADO:
        messages.add_message(request, messages.WARNING, 'Esse período já está fechado.')
        return _redirect_painel(periodo)

    if request.method == 'POST':
        from ativos.models import Equipamentos
        equipamento = get_object_or_404(Equipamentos, id=request.POST.get('equipamento'))
        try:
            medicao = servicos.abrir_medicao_ceq(periodo, equipamento, request.user)
        except servicos.AberturaInvalida as erro:
            messages.add_message(request, messages.ERROR, str(erro))
            return redirect('medicao_equip_ceq_nova_medicao_direta', periodo_id=periodo.id)
        return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)

    equipamentos = servicos.equipamentos_disponiveis_para_medicao(periodo)
    return render(request, 'medicao_equip_ceq_nova_medicao_direta.html', {
        'periodo': periodo, 'equipamentos': equipamentos,
    })


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_fechar_direto(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    medicao = get_object_or_404(MedicaoEquipamento, id=medicao_id)
    try:
        servicos.fechar_medicao_ceq(medicao, request.user)
        messages.add_message(request, messages.SUCCESS, 'Medição fechada.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_ajuste(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado

    medicao = get_object_or_404(
        MedicaoEquipamento.objects.select_related('equipamento', 'obra', 'periodo'), id=medicao_id
    )

    if medicao.status == MedicaoEquipamento.STATUS_ENVIADA:
        servicos.iniciar_analise(medicao, request.user)
        medicao.refresh_from_db()

    linha = servicos.linha_painel(medicao)
    obras_map = {o.id: o for o in Obras.objects.filter(id__in=linha['consolidado'].dias_por_obra.keys())}
    dias_por_obra = [
        {'obra': obras_map[obra_id], 'dias': dias}
        for obra_id, dias in linha['consolidado'].dias_por_obra.items()
    ]

    return render(request, 'medicao_equip_ceq_ajuste.html', {
        'medicao': medicao,
        'apontamentos': medicao.apontamentos.select_related('motivo_parada', 'obra_do_dia').order_by('data'),
        'consolidado': linha['consolidado'], 'divergencia': linha['divergencia'],
        'valor_total': linha['valor_total'], 'valor_manutencao': linha['valor_manutencao'],
        'valor_disposicao': linha['valor_disposicao'],
        'dias_por_obra': dias_por_obra,
        'ajustes_existentes': medicao.ajustes_admin.select_related('obra', 'autor').order_by('-data'),
        'lancamentos_manutencao': medicao.lancamentos_manutencao.select_related('autor').order_by('-data_lancamento'),
        'lancamentos_disposicao': medicao.lancamentos_disposicao.select_related('autor').order_by('-data_lancamento'),
        'historico': medicao.historico.select_related('usuario').all(),
    })


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_aprovar(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    medicao = get_object_or_404(MedicaoEquipamento, id=medicao_id)
    try:
        servicos.aprovar_sem_ajuste(medicao, request.user)
        messages.add_message(request, messages.SUCCESS, 'Medição aprovada e fechada sem ajuste.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_ajustar_devolver(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado

    medicao = get_object_or_404(MedicaoEquipamento.objects.select_related('periodo'), id=medicao_id)
    consolidado, _ = servicos.divergencia_medicao(medicao)

    ajustes = []
    for obra_id, dias_apontados in consolidado.dias_por_obra.items():
        bruto = request.POST.get(f'obra_{obra_id}_dias')
        if bruto is None or bruto.strip() == '':
            continue
        try:
            novo = Decimal(bruto.strip().replace(',', '.'))
        except InvalidOperation:
            messages.add_message(request, messages.ERROR, 'Valor de dias inválido em um dos ajustes.')
            return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)
        if novo == dias_apontados:
            continue
        ajustes.append({
            'obra': get_object_or_404(Obras, id=obra_id),
            'dias_apontados_obra': dias_apontados,
            'dias_aplicados_admin': novo,
            'justificativa': request.POST.get(f'obra_{obra_id}_justificativa', ''),
        })

    try:
        servicos.ajustar_e_devolver(medicao, request.user, ajustes)
        messages.add_message(request, messages.SUCCESS, 'Medição devolvida para a obra com os ajustes registrados.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))

    return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_lancar_manutencao(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    medicao = get_object_or_404(MedicaoEquipamento, id=medicao_id)
    try:
        servicos.lancar_manutencao_admin(medicao, request.user, request.POST.get('dias'), request.POST.get('justificativa'))
        messages.add_message(request, messages.SUCCESS, 'Dias de manutenção lançados.')
    except servicos.ValidacaoLancamento as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_lancar_disposicao(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    medicao = get_object_or_404(MedicaoEquipamento, id=medicao_id)
    try:
        servicos.lancar_disposicao_admin(medicao, request.user, request.POST.get('dias'), request.POST.get('justificativa'))
        messages.add_message(request, messages.SUCCESS, 'Dias à disposição lançados.')
    except servicos.ValidacaoLancamento as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_reabrir_medicao(request, medicao_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    medicao = get_object_or_404(MedicaoEquipamento, id=medicao_id)
    try:
        servicos.reabrir_medicao(medicao, request.user, request.POST.get('justificativa'))
        messages.add_message(request, messages.INFO, 'Medição reaberta.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_fechar_periodo(request, periodo_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    try:
        servicos.fechar_periodo(periodo)
        messages.add_message(request, messages.SUCCESS, 'Período fechado.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return _redirect_painel(periodo)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_equip_ceq_reabrir_periodo(request, periodo_id):
    negado = _get_ceq(request)
    if negado:
        return negado
    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    try:
        servicos.reabrir_periodo(periodo)
        messages.add_message(request, messages.INFO, 'Período reaberto.')
    except servicos.TransicaoInvalida as erro:
        messages.add_message(request, messages.ERROR, str(erro))
    return _redirect_painel(periodo)
