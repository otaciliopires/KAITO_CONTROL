import calendar
from dataclasses import dataclass
from datetime import date

from django.db.models import Sum

from controleCEQ.models import Abastecimento, Entrada
from .models import ParametroTaxaDiesel

MESES_PT = [
    '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]


def fim_mes(ano, mes):
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, ultimo_dia)


def mes_encerrado(ano, mes):
    """True quando o mês (ano, mes) já terminou no calendário — só meses
    encerrados podem ser fechados, já que o mês corrente ainda pode
    receber novos abastecimentos."""
    hoje = date.today()
    return (ano, mes) < (hoje.year, hoje.month)


def _mais_recente(itens, campo_data):
    if not itens:
        return None
    return max(itens, key=lambda item: getattr(item, campo_data))


def _vigente_em(itens, campo_data, ano, mes):
    fim = fim_mes(ano, mes)
    candidatos = [item for item in itens if getattr(item, campo_data) <= fim]
    return _mais_recente(candidatos, campo_data)


@dataclass
class PeriodoMedicao:
    ano: int
    mes: int
    total_abastecimentos_caminhao: int
    total_abastecimentos_obra: int
    fracao: float
    valor_mensal_caminhao: float
    valor_locacao: float
    litros_diesel_obra: float
    preco_diesel_referencia: float
    percentual_taxa_diesel: float
    valor_taxa_diesel: float
    abastecimentos: object = None
    litros_via_caminhao: float = 0.0

    @property
    def nome_mes(self):
        return MESES_PT[self.mes]

    @property
    def fracao_percentual(self):
        return self.fracao * 100

    @property
    def total(self):
        return self.valor_locacao + self.valor_taxa_diesel

    @property
    def preco_unitario_taxa_diesel(self):
        return self.preco_diesel_referencia * (self.percentual_taxa_diesel / 100)


@dataclass
class AcumuladoMedicao:
    numero: int
    quantidade_anterior_locacao: float
    valor_anterior_locacao: float
    quantidade_anterior_diesel: float
    valor_anterior_diesel: float
    periodo: PeriodoMedicao

    @property
    def quantidade_acumulada_locacao(self):
        return self.quantidade_anterior_locacao + self.periodo.fracao

    @property
    def valor_acumulado_locacao(self):
        return self.valor_anterior_locacao + self.periodo.valor_locacao

    @property
    def quantidade_acumulada_diesel(self):
        return self.quantidade_anterior_diesel + self.periodo.litros_diesel_obra

    @property
    def valor_acumulado_diesel(self):
        return self.valor_anterior_diesel + self.periodo.valor_taxa_diesel

    @property
    def total_anterior(self):
        return self.valor_anterior_locacao + self.valor_anterior_diesel

    @property
    def total_periodo(self):
        return self.periodo.total

    @property
    def total_acumulado(self):
        return self.valor_acumulado_locacao + self.valor_acumulado_diesel


def _preco_diesel_referencia(obra):
    entrada = (
        Entrada.objects.filter(obra=obra)
        .order_by('-data_entrega', '-id')
        .first()
    )
    return entrada.preco_unitario if entrada else 0.0


def calcular_periodo(contrato, ano, mes, incluir_tabela=True):
    tanque = contrato.caminhao.tanque
    obra = contrato.obra

    total_caminhao = Abastecimento.objects.filter(
        tanque=tanque, data__year=ano, data__month=mes,
    ).count()

    base_obra_qs = Abastecimento.objects.filter(
        tanque=tanque, obra=obra, data__year=ano, data__month=mes,
    )
    total_obra = base_obra_qs.count()
    fracao = (total_obra / total_caminhao) if total_caminhao else 0.0

    valor_registro = _vigente_em(list(contrato.caminhao.valores_mensais.all()), 'vigente_desde', ano, mes)
    valor_mensal = valor_registro.valor if valor_registro else 0.0
    valor_locacao = fracao * valor_mensal

    litros_diesel = Abastecimento.objects.filter(
        obra=obra, data__year=ano, data__month=mes,
    ).aggregate(total=Sum('litros'))['total'] or 0.0

    preco_diesel = _preco_diesel_referencia(obra)

    percentual_registro = _vigente_em(list(ParametroTaxaDiesel.objects.all()), 'vigente_desde', ano, mes)
    percentual = percentual_registro.percentual if percentual_registro else 0.0

    valor_taxa_diesel = litros_diesel * preco_diesel * (percentual / 100)

    abastecimentos = None
    litros_via_caminhao = 0.0
    if incluir_tabela:
        abastecimentos = base_obra_qs.select_related('equipamento', 'colaborador', 'tanque').order_by('data', 'numero')
        litros_via_caminhao = base_obra_qs.aggregate(total=Sum('litros'))['total'] or 0.0

    return PeriodoMedicao(
        ano=ano, mes=mes,
        total_abastecimentos_caminhao=total_caminhao,
        total_abastecimentos_obra=total_obra,
        fracao=fracao,
        valor_mensal_caminhao=valor_mensal,
        valor_locacao=valor_locacao,
        litros_diesel_obra=litros_diesel,
        preco_diesel_referencia=preco_diesel,
        percentual_taxa_diesel=percentual,
        valor_taxa_diesel=valor_taxa_diesel,
        abastecimentos=abastecimentos,
        litros_via_caminhao=litros_via_caminhao,
    )


def calcular_acumulado(contrato, ano, mes):
    periodo_atual = calcular_periodo(contrato, ano, mes)

    return AcumuladoMedicao(
        numero=contrato.numero_anterior + 1,
        quantidade_anterior_locacao=contrato.quantidade_anterior_locacao,
        valor_anterior_locacao=contrato.valor_anterior_locacao,
        quantidade_anterior_diesel=contrato.quantidade_anterior_diesel,
        valor_anterior_diesel=contrato.valor_anterior_diesel,
        periodo=periodo_atual,
    )


def meses_do_ano(contrato, ano):
    hoje = date.today()
    inicio = contrato.mes_referencia_inicial
    fechados = set(contrato.fechamentos.filter(ano=ano).values_list('mes', flat=True))
    resultado = []
    for mes in range(1, 13):
        disponivel = (ano, mes) >= (inicio.year, inicio.month) and (ano, mes) <= (hoje.year, hoje.month)
        item = {
            'mes': mes, 'nome': MESES_PT[mes], 'disponivel': disponivel,
            'periodo': None, 'fechado': mes in fechados,
        }
        if disponivel:
            item['periodo'] = calcular_periodo(contrato, ano, mes, incluir_tabela=False)
        resultado.append(item)
    return resultado
