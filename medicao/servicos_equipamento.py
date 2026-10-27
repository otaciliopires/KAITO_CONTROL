"""
Serviços da medição de equipamentos: orquestram models_equipamento.py +
calculos_equipamento.py. Toda escrita de estado relevante (abrir medição,
salvar um dia, transições de status) passa por aqui — nunca um save() solto
direto na view.

Isolado do fluxo de caminhão: não importa nem usa ContratoMedicaoCaminhao,
ValorMensalCaminhao, FechamentoMedicaoCaminhao ou qualquer lógica de caminhão.
"""
import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from . import calculos_equipamento as calc
from .models_equipamento import (
    AjusteAdminEquipamento,
    ApontamentoDiarioEquipamento,
    HistoricoMedicaoEquipamento,
    LancamentoDisposicaoEquipamento,
    LancamentoManutencaoEquipamento,
    MedicaoEquipamento,
    PeriodoMedicaoEquipamento,
    ValorMensalEquipamento,
)


class TransicaoInvalida(Exception):
    pass


class AberturaInvalida(Exception):
    pass


class ValidacaoDia(Exception):
    pass


class ValidacaoLancamento(Exception):
    pass


def _registrar_historico(medicao, usuario, campo, valor_anterior, valor_novo, observacao=""):
    HistoricoMedicaoEquipamento.objects.create(
        medicao=medicao, usuario=usuario, campo=campo,
        valor_anterior=str(valor_anterior), valor_novo=str(valor_novo), observacao=observacao,
    )


# --- Períodos ---------------------------------------------------------------

def obter_ou_criar_periodo(ano: int, mes: int) -> PeriodoMedicaoEquipamento:
    dias_do_mes = calendar.monthrange(ano, mes)[1]
    periodo, _criado = PeriodoMedicaoEquipamento.objects.get_or_create(
        ano=ano, mes=mes,
        defaults={
            'data_inicio': date(ano, mes, 1),
            'data_fim': date(ano, mes, dias_do_mes),
            'dias_do_mes': dias_do_mes,
        },
    )
    return periodo


def resumo_status_por_periodo(obra) -> dict:
    """{periodo_id: {status: quantidade}} das medições abertas por essa obra."""
    resumo = defaultdict(lambda: defaultdict(int))
    qs = MedicaoEquipamento.objects.filter(obra=obra).values('periodo_id', 'status')
    for linha in qs.iterator():
        resumo[linha['periodo_id']][linha['status']] += 1
    return resumo


def medicoes_da_obra(periodo, obra):
    return (
        MedicaoEquipamento.objects
        .filter(periodo=periodo, obra=obra)
        .select_related('equipamento')
        .order_by('equipamento__prefixo')
    )


# --- Abertura de medição ------------------------------------------------

def equipamentos_disponiveis_para_medicao(periodo, obra=None):
    """Equipamentos elegíveis, que não são caminhão-abastecedor (via
    VinculoCaminhaoEquipamento) e que ainda podem ganhar uma nova medição
    neste período.

    Com obra informada (fluxo da obra): exclui equipamentos que essa MESMA
    obra já mediu neste período, e os que já têm uma medição direta da
    Central (sem obra) — nesse caso a máquina está marcada como parada o mês
    inteiro, nenhuma obra pode abrir medição própria por cima.
    Sem obra (fluxo da Central / medição direta): exclui equipamentos que já
    têm QUALQUER medição neste período, de qualquer obra — a medição direta
    da Central só serve para máquina totalmente parada, sem nenhuma obra
    envolvida no mês.
    """
    from ativos.models import Equipamentos

    if obra is None:
        ja_medidos = MedicaoEquipamento.objects.filter(periodo=periodo).values_list('equipamento_id', flat=True)
    else:
        ja_medidos = (
            MedicaoEquipamento.objects
            .filter(periodo=periodo)
            .filter(models.Q(obra=obra) | models.Q(obra__isnull=True))
            .values_list('equipamento_id', flat=True)
        )

    return (
        Equipamentos.objects
        .filter(elegivel_medicao=True)
        .exclude(vinculo_caminhao__isnull=False)
        .exclude(id__in=ja_medidos)
        .order_by('prefixo')
    )


@transaction.atomic
def abrir_medicao(periodo, equipamento, obra, usuario) -> MedicaoEquipamento:
    if periodo.status == PeriodoMedicaoEquipamento.STATUS_FECHADO:
        raise AberturaInvalida(f"O período {periodo} já está fechado — não é possível abrir novas medições.")
    if not equipamento.elegivel_medicao:
        raise AberturaInvalida(f"{equipamento.prefixo} não está marcado como elegível para medição.")
    if hasattr(equipamento, 'vinculo_caminhao'):
        raise AberturaInvalida(
            f"{equipamento.prefixo} é um caminhão-abastecedor — medido pelo fluxo de caminhão, não aqui."
        )
    if MedicaoEquipamento.objects.filter(periodo=periodo, equipamento=equipamento, obra__isnull=True).exists():
        raise AberturaInvalida(
            f"{equipamento.prefixo} está com medição aberta direto pela Central (sem obra) em {periodo} — "
            "marcado como parado o período inteiro, nenhuma obra pode medi-lo."
        )
    if MedicaoEquipamento.objects.filter(periodo=periodo, equipamento=equipamento, obra=obra).exists():
        raise AberturaInvalida(f"{equipamento.prefixo} já tem uma medição aberta em {periodo} para esta obra.")

    valor_vigente = (
        ValorMensalEquipamento.objects
        .filter(equipamento=equipamento, vigente_desde__lte=timezone.now().date())
        .order_by('-vigente_desde')
        .first()
    )
    if valor_vigente is None:
        raise AberturaInvalida(f"{equipamento.prefixo} não tem valor de aluguel cadastrado.")

    medicao = MedicaoEquipamento.objects.create(
        periodo=periodo, equipamento=equipamento, obra=obra,
        valor_aluguel_vigente=valor_vigente.valor,
        status=MedicaoEquipamento.STATUS_RASCUNHO,
    )

    dias = []
    dia_atual = periodo.data_inicio
    while dia_atual <= periodo.data_fim:
        dias.append(ApontamentoDiarioEquipamento(medicao=medicao, data=dia_atual, obra_do_dia=obra))
        dia_atual += timedelta(days=1)
    ApontamentoDiarioEquipamento.objects.bulk_create(dias)

    _registrar_historico(medicao, usuario, 'abertura', '', f"RASCUNHO - {equipamento.prefixo} / {obra.nome}")
    return medicao


@transaction.atomic
def abrir_medicao_ceq(periodo, equipamento, usuario) -> MedicaoEquipamento:
    """Abre uma medição SEM obra, direto pela Central — para quando o
    equipamento passa o período inteiro parado (manutenção e/ou à
    disposição), sem nenhuma obra envolvida (ex.: máquina que fica meses na
    oficina). Sem obra não há grade diária nem fluxo de envio/análise: a
    Central só lança os dias de manutenção/disposição em lote
    (lancar_manutencao_admin / lancar_disposicao_admin) e fecha direto
    (fechar_medicao_ceq) quando completar o mês."""
    if periodo.status == PeriodoMedicaoEquipamento.STATUS_FECHADO:
        raise AberturaInvalida(f"O período {periodo} já está fechado — não é possível abrir novas medições.")
    if not equipamento.elegivel_medicao:
        raise AberturaInvalida(f"{equipamento.prefixo} não está marcado como elegível para medição.")
    if hasattr(equipamento, 'vinculo_caminhao'):
        raise AberturaInvalida(
            f"{equipamento.prefixo} é um caminhão-abastecedor — medido pelo fluxo de caminhão, não aqui."
        )
    if MedicaoEquipamento.objects.filter(periodo=periodo, equipamento=equipamento).exists():
        raise AberturaInvalida(f"{equipamento.prefixo} já tem uma medição aberta em {periodo}.")

    valor_vigente = (
        ValorMensalEquipamento.objects
        .filter(equipamento=equipamento, vigente_desde__lte=timezone.now().date())
        .order_by('-vigente_desde')
        .first()
    )
    if valor_vigente is None:
        raise AberturaInvalida(f"{equipamento.prefixo} não tem valor de aluguel cadastrado.")

    medicao = MedicaoEquipamento.objects.create(
        periodo=periodo, equipamento=equipamento, obra=None,
        valor_aluguel_vigente=valor_vigente.valor,
        status=MedicaoEquipamento.STATUS_RASCUNHO,
    )
    _registrar_historico(
        medicao, usuario, 'abertura', '',
        f"RASCUNHO - {equipamento.prefixo} / Central (sem obra)",
    )
    return medicao


@transaction.atomic
def fechar_medicao_ceq(medicao, usuario) -> MedicaoEquipamento:
    """Fecha direto uma medição sem obra (aberta via abrir_medicao_ceq). Sem
    obra não existe envio/análise/devolução para fechar — a Central fecha
    assim que os lançamentos de manutenção/disposição completarem o mês."""
    if medicao.obra_id is not None:
        raise TransicaoInvalida("Essa medição tem obra responsável — feche pelo fluxo normal de análise.")
    if medicao.status == MedicaoEquipamento.STATUS_FECHADA:
        raise TransicaoInvalida("Medição já está fechada.")
    _, divergencia = divergencia_medicao(medicao)
    if divergencia != 0:
        raise TransicaoInvalida(
            f"Não é possível fechar: divergência de {divergencia} dia(s) em relação ao mês. "
            "Complete os lançamentos de manutenção/disposição antes de fechar."
        )
    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_FECHADA
    medicao.fechada_em = timezone.now()
    medicao.fechada_por = usuario
    medicao.save(update_fields=['status', 'fechada_em', 'fechada_por', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status, observacao='Fechada direto pela Central (sem obra)')
    return medicao


# --- Lançamento diário --------------------------------------------------

def salvar_dia(apontamento, *, contador_inicial, contador_final, parada_horas, motivo, obra_do_dia, observacoes=""):
    """Recalcula e grava um dia da grade a partir de dados brutos. O
    fracao_calculada e o tipo_dia NUNCA vêm do formulário — são sempre
    recalculados aqui, que é a fonte da verdade.

    Retorna (apontamento, avisos) em sucesso. Levanta ValidacaoDia em erro
    bloqueante (nada é salvo nesse caso).
    """
    if apontamento.medicao.status != MedicaoEquipamento.STATUS_RASCUNHO:
        raise ValidacaoDia("Medição não está em rascunho — a obra não pode mais editar os dias.")

    avisos = []

    if contador_final is None:
        apontamento.contador_inicial = None
        apontamento.contador_final = None
        apontamento.tempo_parada_horas = Decimal('0')
        apontamento.motivo_parada = None
        apontamento.obra_do_dia = obra_do_dia
        apontamento.tipo_dia = None
        apontamento.fracao_calculada = None
        apontamento.fracao_ajustada = None
        apontamento.observacoes = observacoes
        apontamento.save()
        return apontamento, avisos

    if contador_inicial is None:
        raise ValidacaoDia("Informe o contador inicial do dia.")
    if contador_final < contador_inicial:
        raise ValidacaoDia("Contador final não pode ser menor que o inicial.")

    parada_horas = parada_horas if parada_horas is not None else Decimal('0')
    jornada = calc.jornada_util_horas()

    if parada_horas > jornada:
        raise ValidacaoDia("Tempo de parada não pode ser maior que a jornada útil do dia.")
    if parada_horas > 0 and motivo is None:
        raise ValidacaoDia("Informe o motivo da parada.")

    equipamento = apontamento.medicao.equipamento
    if equipamento.unidade_medicao == 'H':
        horas_trabalhadas = contador_final - contador_inicial
        if horas_trabalhadas > 24:
            avisos.append("Variação de horímetro maior que 24h no dia — confira a leitura.")
        fracao = calc.calcular_fracao_horimetro(parada_horas, horas_trabalhadas, jornada)
    else:
        variacao = contador_final - contador_inicial
        limite_km = Decimal(str(getattr(settings, 'MEDICAO_EQUIP_KM_DIARIO_ALERTA', 800)))
        if variacao > limite_km:
            avisos.append(f"Variação de odômetro maior que {limite_km} km no dia — confira a leitura.")
        fracao = calc.calcular_fracao_odometro(parada_horas, jornada)

    destino = motivo.destino_complemento if motivo else None
    tipo_dia = calc.derivar_tipo_dia(fracao, destino)

    dia_anterior = (
        ApontamentoDiarioEquipamento.objects
        .filter(medicao=apontamento.medicao, data__lt=apontamento.data)
        .order_by('-data')
        .first()
    )
    if dia_anterior is not None and dia_anterior.contador_final is not None:
        if dia_anterior.contador_final != contador_inicial:
            avisos.append(
                f"Contador inicial ({contador_inicial}) não bate com o final do dia anterior "
                f"({dia_anterior.contador_final})."
            )

    apontamento.contador_inicial = contador_inicial
    apontamento.contador_final = contador_final
    apontamento.tempo_parada_horas = parada_horas
    apontamento.motivo_parada = motivo
    apontamento.obra_do_dia = obra_do_dia
    apontamento.tipo_dia = tipo_dia
    apontamento.fracao_calculada = fracao
    apontamento.fracao_ajustada = None
    apontamento.observacoes = observacoes
    apontamento.save()
    return apontamento, avisos


# --- Consolidação (ponte ORM -> calculos_equipamento) --------------------

def consolidar_medicao(medicao) -> calc.ConsolidadoEquipamento:
    """`obra_do_dia` é só uma informação da obra sobre onde a máquina rodou
    naquele dia — nunca decide quem é cobrado. Todo dia de trabalho de uma
    medição é sempre atribuído à obra responsável pela própria medição
    (medicao.obra), a mesma que a abriu: uma obra não pode redirecionar a
    cobrança de um dia para outra obra só escolhendo-a no formulário."""
    entradas = []
    for ap in medicao.apontamentos.all():
        if not ap.preenchido or ap.fracao is None or ap.tipo_dia is None:
            continue
        if ap.tipo_dia == calc.TIPO_TRABALHO:
            destino = ap.motivo_parada.destino_complemento if ap.motivo_parada else None
            complemento = calc.classificar_complemento(ap.fracao, destino)
            entradas.append(calc.ApontamentoParaConsolidar(
                obra_id=medicao.obra_id, dias_obra=ap.fracao,
                dias_manutencao=complemento.dias_manutencao, dias_disposicao=complemento.dias_disposicao,
            ))
        elif ap.tipo_dia == calc.TIPO_MANUTENCAO:
            entradas.append(calc.ApontamentoParaConsolidar(
                obra_id=medicao.obra_id, dias_obra=Decimal('0.00'),
                dias_manutencao=Decimal('1.00'), dias_disposicao=Decimal('0.00'),
            ))
        elif ap.tipo_dia == calc.TIPO_DISPOSICAO:
            entradas.append(calc.ApontamentoParaConsolidar(
                obra_id=medicao.obra_id, dias_obra=Decimal('0.00'),
                dias_manutencao=Decimal('0.00'), dias_disposicao=Decimal('1.00'),
            ))
    return calc.consolidar_mes(entradas)


def consolidar_medicao_com_ajustes(medicao) -> calc.ConsolidadoEquipamento:
    """Como consolidar_medicao, mas com os dias_por_obra sobrescritos pelo
    último AjusteAdminEquipamento de cada obra (quando existir), e os
    lançamentos administrativos de manutenção/disposição somados por cima
    dos apurados a partir da grade diária."""
    bruto = consolidar_medicao(medicao)

    dias_por_obra = dict(bruto.dias_por_obra)
    for ajuste in medicao.ajustes_admin.order_by('data'):
        dias_por_obra[ajuste.obra_id] = ajuste.dias_aplicados_admin

    dias_manutencao = bruto.dias_manutencao + sum(
        (l.dias for l in medicao.lancamentos_manutencao.all()), Decimal('0.00')
    )
    dias_disposicao = bruto.dias_disposicao + sum(
        (l.dias for l in medicao.lancamentos_disposicao.all()), Decimal('0.00')
    )
    return calc.ConsolidadoEquipamento(
        dias_por_obra=dias_por_obra, dias_manutencao=dias_manutencao, dias_disposicao=dias_disposicao
    )


def divergencia_medicao(medicao):
    """Consolidado e divergência usando SEMPRE a visão com ajustes — é o que
    vale para decidir se uma medição pode ser fechada (obra ou CEQ)."""
    consolidado = consolidar_medicao_com_ajustes(medicao)
    divergencia = calc.calcular_divergencia_fechamento(consolidado, medicao.periodo.dias_do_mes)
    return consolidado, divergencia


# --- Transições de status (obra) -----------------------------------------

@transaction.atomic
def enviar_para_central(medicao, usuario) -> MedicaoEquipamento:
    if medicao.status != MedicaoEquipamento.STATUS_RASCUNHO:
        raise TransicaoInvalida("Só é possível enviar uma medição em RASCUNHO.")
    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_ENVIADA
    medicao.enviada_em = timezone.now()
    medicao.enviada_por = usuario
    medicao.save(update_fields=['status', 'enviada_em', 'enviada_por', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status)
    return medicao


@transaction.atomic
def confirmar_e_fechar(medicao, usuario) -> MedicaoEquipamento:
    if medicao.status != MedicaoEquipamento.STATUS_DEVOLVIDA:
        raise TransicaoInvalida("Só é possível confirmar uma medição DEVOLVIDA.")
    _, divergencia = divergencia_medicao(medicao)
    if divergencia != 0:
        raise TransicaoInvalida(
            f"Não é possível fechar: divergência de {divergencia} dia(s) em relação ao mês. "
            "Conteste para a Central corrigir antes de confirmar."
        )
    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_FECHADA
    medicao.fechada_em = timezone.now()
    medicao.fechada_por = usuario
    medicao.save(update_fields=['status', 'fechada_em', 'fechada_por', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status)
    return medicao


@transaction.atomic
def contestar(medicao, usuario, justificativa: str) -> MedicaoEquipamento:
    if medicao.status != MedicaoEquipamento.STATUS_DEVOLVIDA:
        raise TransicaoInvalida("Só é possível contestar uma medição DEVOLVIDA.")
    justificativa = (justificativa or '').strip()
    if not justificativa:
        raise TransicaoInvalida("Justificativa é obrigatória para contestar.")
    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_EM_ANALISE
    medicao.save(update_fields=['status', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status, observacao=justificativa)
    return medicao


# --- Transições de status (CEQ / admin) -----------------------------------

@transaction.atomic
def iniciar_analise(medicao, usuario) -> MedicaoEquipamento:
    """ENVIADA -> EM_ANALISE. Chamado automaticamente quando a Central abre a
    tela de ajuste de uma medição enviada — não exige um clique à parte."""
    if medicao.status != MedicaoEquipamento.STATUS_ENVIADA:
        raise TransicaoInvalida("Só é possível iniciar análise de uma medição ENVIADA.")
    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_EM_ANALISE
    medicao.analisada_em = timezone.now()
    medicao.analisada_por = usuario
    medicao.save(update_fields=['status', 'analisada_em', 'analisada_por', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status)
    return medicao


@transaction.atomic
def aprovar_sem_ajuste(medicao, usuario) -> MedicaoEquipamento:
    if medicao.status != MedicaoEquipamento.STATUS_EM_ANALISE:
        raise TransicaoInvalida("Só é possível aprovar uma medição EM_ANALISE.")
    _, divergencia = divergencia_medicao(medicao)
    if divergencia != 0:
        raise TransicaoInvalida(
            f"Não é possível fechar: divergência de {divergencia} dia(s) em relação ao mês. "
            "Ajuste os lançamentos (ou lance manutenção/disposição) antes de aprovar."
        )
    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_FECHADA
    medicao.fechada_em = timezone.now()
    medicao.fechada_por = usuario
    medicao.save(update_fields=['status', 'fechada_em', 'fechada_por', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status, observacao='Aprovada sem ajuste')
    return medicao


@transaction.atomic
def ajustar_e_devolver(medicao, usuario, ajustes) -> MedicaoEquipamento:
    """ajustes: lista de dicts {obra, dias_apontados_obra, dias_aplicados_admin,
    justificativa} — um item por obra realmente sobrescrita (não é preciso
    informar as obras que ficam como apurado)."""
    if medicao.status != MedicaoEquipamento.STATUS_EM_ANALISE:
        raise TransicaoInvalida("Só é possível ajustar uma medição EM_ANALISE.")
    if not ajustes:
        raise TransicaoInvalida(
            "Nenhum ajuste informado. Se está tudo certo, use \"Aprovar sem ajuste\"."
        )
    for item in ajustes:
        justificativa = (item.get('justificativa') or '').strip()
        if not justificativa:
            raise TransicaoInvalida(f"Justificativa obrigatória para o ajuste da obra {item['obra']}.")
        AjusteAdminEquipamento.objects.create(
            medicao=medicao, obra=item['obra'],
            dias_apontados_obra=item['dias_apontados_obra'],
            dias_aplicados_admin=item['dias_aplicados_admin'],
            justificativa=justificativa, autor=usuario,
        )

    status_anterior = medicao.status
    medicao.status = MedicaoEquipamento.STATUS_DEVOLVIDA
    medicao.devolvida_em = timezone.now()
    medicao.devolvida_por = usuario
    medicao.save(update_fields=['status', 'devolvida_em', 'devolvida_por', 'atualizado_em'])
    resumo = "; ".join(f"{item['obra'].nome}: {item['dias_apontados_obra']} -> {item['dias_aplicados_admin']}" for item in ajustes)
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status, observacao=resumo)
    return medicao


@transaction.atomic
def reabrir_medicao(medicao, usuario, justificativa: str) -> MedicaoEquipamento:
    if medicao.status != MedicaoEquipamento.STATUS_FECHADA:
        raise TransicaoInvalida("Só é possível reabrir uma medição FECHADA.")
    justificativa = (justificativa or '').strip()
    if not justificativa:
        raise TransicaoInvalida("Justificativa é obrigatória para reabrir.")
    status_anterior = medicao.status
    # sem obra não existe "análise" de dados de obra — volta direto pra edição livre da Central
    medicao.status = MedicaoEquipamento.STATUS_RASCUNHO if medicao.obra_id is None else MedicaoEquipamento.STATUS_EM_ANALISE
    medicao.reaberta_em = timezone.now()
    medicao.reaberta_por = usuario
    medicao.save(update_fields=['status', 'reaberta_em', 'reaberta_por', 'atualizado_em'])
    _registrar_historico(medicao, usuario, 'status', status_anterior, medicao.status, observacao=justificativa)
    return medicao


def lancar_manutencao_admin(medicao, usuario, dias, justificativa) -> LancamentoManutencaoEquipamento:
    return _lancar_admin(LancamentoManutencaoEquipamento, medicao, usuario, dias, justificativa)


def lancar_disposicao_admin(medicao, usuario, dias, justificativa) -> LancamentoDisposicaoEquipamento:
    return _lancar_admin(LancamentoDisposicaoEquipamento, medicao, usuario, dias, justificativa)


def _lancar_admin(modelo, medicao, usuario, dias, justificativa):
    try:
        dias = Decimal(dias)
    except Exception:
        raise ValidacaoLancamento("Quantidade de dias inválida.")
    if dias <= 0:
        raise ValidacaoLancamento("Dias deve ser maior que zero.")
    justificativa = (justificativa or '').strip()
    if not justificativa:
        raise ValidacaoLancamento("Justificativa é obrigatória.")
    return modelo.objects.create(
        medicao=medicao, dias=dias, origem=modelo.ORIGEM_ADMIN,
        justificativa=justificativa, autor=usuario,
    )


# --- Fechamento / reabertura de período (global, todas as obras) ----------

@transaction.atomic
def fechar_periodo(periodo) -> PeriodoMedicaoEquipamento:
    if periodo.status == PeriodoMedicaoEquipamento.STATUS_FECHADO:
        raise TransicaoInvalida("Período já está fechado.")
    pendentes = (
        MedicaoEquipamento.objects.filter(periodo=periodo)
        .exclude(status=MedicaoEquipamento.STATUS_FECHADA)
        .select_related('equipamento')
    )
    if pendentes.exists():
        nomes = ", ".join(f"{m.equipamento.prefixo} ({m.get_status_display()})" for m in pendentes)
        raise TransicaoInvalida(f"Ainda há medições não fechadas neste período: {nomes}.")
    periodo.status = PeriodoMedicaoEquipamento.STATUS_FECHADO
    periodo.save(update_fields=['status'])
    return periodo


@transaction.atomic
def reabrir_periodo(periodo) -> PeriodoMedicaoEquipamento:
    if periodo.status != PeriodoMedicaoEquipamento.STATUS_FECHADO:
        raise TransicaoInvalida("Período não está fechado.")
    periodo.status = PeriodoMedicaoEquipamento.STATUS_ABERTO
    periodo.save(update_fields=['status'])
    return periodo


# --- Painel do CEQ ----------------------------------------------------------

def medicoes_do_periodo(periodo):
    return (
        MedicaoEquipamento.objects.filter(periodo=periodo)
        .select_related('equipamento', 'obra')
        .order_by('equipamento__prefixo')
    )


def linha_painel(medicao) -> dict:
    """Dados prontos (já com valores em R$) para uma linha do painel do CEQ
    ou da tela de ajuste de uma medição."""
    consolidado, divergencia = divergencia_medicao(medicao)
    dias_do_mes = medicao.periodo.dias_do_mes
    valor_obra_total = sum(
        (
            calc.calcular_valor_rateio(dias, dias_do_mes, medicao.valor_aluguel_vigente)
            for dias in consolidado.dias_por_obra.values()
        ),
        Decimal('0.00'),
    )
    valor_manutencao = calc.calcular_valor_rateio(consolidado.dias_manutencao, dias_do_mes, medicao.valor_aluguel_vigente)
    valor_disposicao = calc.calcular_valor_rateio(consolidado.dias_disposicao, dias_do_mes, medicao.valor_aluguel_vigente)
    return {
        'medicao': medicao,
        'consolidado': consolidado,
        'divergencia': divergencia,
        'valor_obra_total': valor_obra_total,
        'valor_manutencao': valor_manutencao,
        'valor_disposicao': valor_disposicao,
        'valor_total': valor_obra_total + valor_manutencao + valor_disposicao,
    }


def resumo_financeiro(linhas) -> dict:
    """Agrega várias linhas (de linha_painel) em totais por obra + manutenção
    + disposição + total geral do período."""
    from ativos.models import Obras

    por_obra = defaultdict(lambda: Decimal('0.00'))
    manutencao = Decimal('0.00')
    disposicao = Decimal('0.00')

    for linha in linhas:
        medicao = linha['medicao']
        dias_do_mes = medicao.periodo.dias_do_mes
        for obra_id, dias in linha['consolidado'].dias_por_obra.items():
            por_obra[obra_id] += calc.calcular_valor_rateio(dias, dias_do_mes, medicao.valor_aluguel_vigente)
        manutencao += linha['valor_manutencao']
        disposicao += linha['valor_disposicao']

    obras_map = {o.id: o for o in Obras.objects.filter(id__in=por_obra.keys())}
    linhas_por_obra = sorted(
        ({'obra': obras_map.get(oid), 'valor': valor} for oid, valor in por_obra.items()),
        key=lambda l: l['obra'].nome if l['obra'] else '',
    )
    total = sum((l['valor'] for l in linhas_por_obra), Decimal('0.00')) + manutencao + disposicao
    return {'por_obra': linhas_por_obra, 'manutencao': manutencao, 'disposicao': disposicao, 'total': total}


def matriz_localizacao(periodo):
    """Dados para o painel de localização (equivalente à aba LOCALIZAÇÃO da
    planilha legada): uma linha por medição, com os dias em cada obra
    (colunas dinâmicas — uma por obra que aparece no período) + manutenção +
    à disposição + total apurado + divergência."""
    from ativos.models import Obras

    linhas_base = [linha_painel(m) for m in medicoes_do_periodo(periodo)]

    obra_ids = set()
    for linha in linhas_base:
        obra_ids.update(linha['consolidado'].dias_por_obra.keys())
    obras_colunas = list(Obras.objects.filter(id__in=obra_ids).order_by('nome'))

    linhas = []
    for linha in linhas_base:
        consolidado = linha['consolidado']
        linhas.append({
            'medicao': linha['medicao'],
            'dias_por_coluna': [consolidado.dias_por_obra.get(o.id, Decimal('0.00')) for o in obras_colunas],
            'manutencao': consolidado.dias_manutencao,
            'disposicao': consolidado.dias_disposicao,
            'total': consolidado.total_dias,
            'divergencia': linha['divergencia'],
        })

    return obras_colunas, linhas
