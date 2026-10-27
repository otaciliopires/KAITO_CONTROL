"""
Regras de cálculo da medição mensal de equipamentos.

Funções puras, isoladas de models e views: recebem e devolvem apenas Decimal,
str, int e os NamedTuples definidos aqui — nenhum import de ORM, nenhuma
consulta ao banco. Todos os valores monetários e frações usam Decimal, nunca
float.

Isolado do fluxo de medição de caminhão: nada aqui é compartilhado com
ContratoMedicaoCaminhao / ValorMensalCaminhao / cálculo de caminhão.

Os literais DESTINO_MANUTENCAO / DESTINO_DISPOSICAO abaixo precisam
permanecer em sincronia com os values de
`medicao.models_equipamento.MotivoParada.DESTINO_CHOICES` — este módulo não
importa o model de propósito (para ficar puro), então quem chama passa
`motivo.destino_complemento` (uma string) diretamente.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, NamedTuple, Optional

from django.conf import settings

DESTINO_MANUTENCAO = 'MANUTENCAO'
DESTINO_DISPOSICAO = 'DISPOSICAO'

TIPO_TRABALHO = 'TRABALHO'
TIPO_MANUTENCAO = 'MANUTENCAO'
TIPO_DISPOSICAO = 'DISPOSICAO'

_DUAS_CASAS = Decimal('0.01')
_ZERO = Decimal('0.00')
_UM = Decimal('1.00')


def jornada_util_horas() -> Decimal:
    """Jornada útil de referência (horas/dia). Parametrizável via
    settings.JORNADA_UTIL_HORAS (default 9) — nunca hardcoded nas fórmulas."""
    valor = getattr(settings, 'JORNADA_UTIL_HORAS', 9)
    return Decimal(str(valor))


def _arredondar_fracao(fracao: Decimal) -> Decimal:
    fracao = fracao.quantize(_DUAS_CASAS, rounding=ROUND_HALF_UP)
    if fracao < _ZERO:
        return _ZERO
    if fracao > _UM:
        return _UM
    return fracao


def calcular_fracao_horimetro(
    parada_horas: Decimal,
    horas_trabalhadas: Decimal,
    jornada_util: Optional[Decimal] = None,
) -> Decimal:
    """Fração do dia rendida por um equipamento medido a horímetro.

    Sem parada informada, a fração é sempre 1,00 — mesmo com horas
    trabalhadas baixas ou zero (fim de semana, chuva, equipamento parado sem
    apontamento). A fração nunca é derivada das horas trabalhadas nesse caso.

    Com parada, usa o maior entre "jornada útil menos a parada" (quanto
    sobrava de expediente) e as horas realmente trabalhadas — porque o
    equipamento pode compensar a parada trabalhando fora da janela padrão.
    """
    jornada_util = jornada_util_horas() if jornada_util is None else jornada_util
    if parada_horas == 0:
        return _UM
    base = max(jornada_util - parada_horas, horas_trabalhadas)
    return _arredondar_fracao(base / jornada_util)


def calcular_fracao_odometro(
    parada_horas: Decimal,
    jornada_util: Optional[Decimal] = None,
) -> Decimal:
    """Fração do dia rendida por um equipamento medido a odômetro. Não existe
    "horas trabalhadas" para veículo — só o tempo de parada informado conta."""
    jornada_util = jornada_util_horas() if jornada_util is None else jornada_util
    if parada_horas == 0:
        return _UM
    return _arredondar_fracao(_UM - (parada_horas / jornada_util))


def calcular_complemento(fracao_trabalho: Decimal) -> Decimal:
    """Parte do dia que não foi trabalho (1 - fração). Nunca negativa."""
    complemento = _UM - fracao_trabalho
    return complemento if complemento > _ZERO else _ZERO


class ComplementoDia(NamedTuple):
    dias_manutencao: Decimal
    dias_disposicao: Decimal


def classificar_complemento(fracao_trabalho: Decimal, destino_complemento: Optional[str]) -> ComplementoDia:
    """Classifica o complemento do dia (1 - fração de trabalho) em manutenção
    ou à disposição, conforme o destino do motivo de parada informado.

    Motivo do tipo manutenção -> complemento vira dias de manutenção.
    Qualquer outro motivo -> complemento vira dias à disposição (CEQ).
    Dia inteiro perdido (fração 0) cai inteiro na categoria do motivo, nunca
    como dia de obra.
    """
    complemento = calcular_complemento(fracao_trabalho)
    if complemento == _ZERO:
        return ComplementoDia(_ZERO, _ZERO)
    if destino_complemento == DESTINO_MANUTENCAO:
        return ComplementoDia(complemento, _ZERO)
    if destino_complemento == DESTINO_DISPOSICAO:
        return ComplementoDia(_ZERO, complemento)
    raise ValueError(
        "Dia com fração de trabalho < 1 precisa de um motivo de parada com "
        "destino_complemento definido (MANUTENCAO ou DISPOSICAO)."
    )


def derivar_tipo_dia(fracao_trabalho: Decimal, destino_complemento: Optional[str]) -> str:
    """Classifica o dia (TRABALHO / MANUTENCAO / DISPOSICAO) a partir da
    fração de trabalho e, quando ela é zero, do destino do motivo de parada.
    Nunca é uma escolha manual — sempre derivado no save.

    Fração > 0 -> TRABALHO (mesmo que parcial: o complemento vira dias de
    manutenção/disposição à parte, via classificar_complemento, mas o dia em
    si é predominantemente de trabalho).
    Fração == 0 -> cai inteiro na categoria do motivo (nunca como TRABALHO).
    """
    if fracao_trabalho > _ZERO:
        return TIPO_TRABALHO
    if destino_complemento in (DESTINO_MANUTENCAO, DESTINO_DISPOSICAO):
        return destino_complemento
    raise ValueError(
        "Dia com fração de trabalho 0 precisa de um motivo de parada com "
        "destino_complemento definido para derivar o tipo do dia."
    )


def calcular_fator_rateio(dias_apurados: Decimal, dias_do_mes: int) -> Decimal:
    if dias_do_mes <= 0:
        raise ValueError("dias_do_mes deve ser positivo.")
    return dias_apurados / Decimal(dias_do_mes)


def calcular_valor_rateio(dias_apurados: Decimal, dias_do_mes: int, valor_aluguel_mensal: Decimal) -> Decimal:
    """valor = (dias_apurados / dias_do_mes) * valor_aluguel_mensal.

    Vale igualmente para dias de obra, de manutenção e à disposição — a
    mesma fórmula gera o custo de máquina parada por manutenção e o custo de
    máquina parada à disposição.
    """
    fator = calcular_fator_rateio(dias_apurados, dias_do_mes)
    valor = fator * valor_aluguel_mensal
    return valor.quantize(_DUAS_CASAS, rounding=ROUND_HALF_UP)


class ApontamentoParaConsolidar(NamedTuple):
    """Entrada mínima para consolidar um dia já classificado. `obra_id` é
    quem recebe `dias_obra`; dias_manutencao/dias_disposicao não são
    atribuídos a nenhuma obra (viram custo de manutenção/CEQ)."""

    obra_id: int
    dias_obra: Decimal
    dias_manutencao: Decimal
    dias_disposicao: Decimal


class ConsolidadoEquipamento(NamedTuple):
    dias_por_obra: Dict[int, Decimal]
    dias_manutencao: Decimal
    dias_disposicao: Decimal

    @property
    def total_dias(self) -> Decimal:
        total = self.dias_manutencao + self.dias_disposicao
        for dias in self.dias_por_obra.values():
            total += dias
        return total


def consolidar_mes(apontamentos: Iterable[ApontamentoParaConsolidar]) -> ConsolidadoEquipamento:
    """dias_por_obra[obra] = soma das frações de dias de obra apontadas
    naquela obra ao longo do mês; dias_manutencao/dias_disposicao somam à
    parte, sem distinção de obra."""
    dias_por_obra: Dict[int, Decimal] = {}
    dias_manutencao = _ZERO
    dias_disposicao = _ZERO
    for ap in apontamentos:
        if ap.dias_obra:
            dias_por_obra[ap.obra_id] = dias_por_obra.get(ap.obra_id, _ZERO) + ap.dias_obra
        dias_manutencao += ap.dias_manutencao
        dias_disposicao += ap.dias_disposicao
    return ConsolidadoEquipamento(
        dias_por_obra=dias_por_obra,
        dias_manutencao=dias_manutencao,
        dias_disposicao=dias_disposicao,
    )


def calcular_divergencia_fechamento(consolidado: ConsolidadoEquipamento, dias_do_mes: int) -> Decimal:
    """total apurado - dias_do_mes. Zero = fecha certo; diferente de zero =
    erro a sinalizar (bloqueia o fechamento do período)."""
    return consolidado.total_dias - Decimal(dias_do_mes)
