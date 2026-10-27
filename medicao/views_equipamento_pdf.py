"""
Exportação em PDF da medição de equipamentos (boletim por medição + resumo
financeiro do período), com xhtml2pdf — mesmo padrão de
medicao/views.py::medicao_boletim_pdf (fluxo de caminhão) e
controleCEQ/views.py, mas duplicado de propósito: EMPRESA, _logo_data_uri e
os templates são cópias próprias, não importadas do fluxo de caminhão.
"""
import base64
from datetime import date
from functools import lru_cache

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.text import slugify
from xhtml2pdf import pisa

from ativos.models import Obras

from . import calculos_equipamento as calc
from . import servicos_equipamento as servicos
from .models_equipamento import MedicaoEquipamento, PeriodoMedicaoEquipamento

EMPRESA = {
    'nome': 'Construtora Rocha Cavalcante Ltda',
    'cnpj': '09.323.098/0001-92',
    'endereco': 'Rua Álvaro de Araújo Pereira, 255 - Jardim Tavares - Campina Grande - PB',
    'insc_estadual': '16.056.310-0',
    'cidade': 'Campina Grande-PB',
}


@lru_cache(maxsize=1)
def _logo_data_uri():
    caminho = settings.BASE_DIR / 'static' / 'medicao' / 'img' / 'logo_rocha.png'
    if not caminho.exists():
        return ''
    dados = base64.b64encode(caminho.read_bytes()).decode('ascii')
    return f'data:image/png;base64,{dados}'


def _tem_acesso(request, medicao):
    return (
        request.user.is_superuser
        or request.user.status == 'c'
        or (medicao.obra_id is not None and medicao.obra.usuario.filter(id=request.user.id).exists())
    )


def _redirect_detalhe(request, medicao):
    if request.user.is_superuser or request.user.status == 'c':
        return redirect('medicao_equip_ceq_ajuste', medicao_id=medicao.id)
    return redirect('medicao_equip_obra_medicao', medicao_id=medicao.id)


@login_required(login_url='/auth/login/')
def medicao_equip_boletim_pdf(request, medicao_id):
    medicao = get_object_or_404(
        MedicaoEquipamento.objects.select_related('equipamento', 'obra', 'periodo'), id=medicao_id
    )
    if not _tem_acesso(request, medicao):
        return HttpResponse('<h1>Acesso negado</h1>')

    if medicao.status != MedicaoEquipamento.STATUS_FECHADA:
        messages.add_message(request, messages.WARNING, 'Feche a medição antes de baixar o boletim.')
        return _redirect_detalhe(request, medicao)

    linha = servicos.linha_painel(medicao)
    dias_do_mes = medicao.periodo.dias_do_mes
    obras_map = {o.id: o for o in Obras.objects.filter(id__in=linha['consolidado'].dias_por_obra.keys())}
    dias_por_obra = [
        {
            'obra': obras_map[obra_id], 'dias': dias,
            'fator': calc.calcular_fator_rateio(dias, dias_do_mes),
            'valor': calc.calcular_valor_rateio(dias, dias_do_mes, medicao.valor_aluguel_vigente),
        }
        for obra_id, dias in linha['consolidado'].dias_por_obra.items()
    ]

    contexto = {
        'medicao': medicao,
        'equipamento': medicao.equipamento,
        'periodo': medicao.periodo,
        'dias_por_obra': dias_por_obra,
        'consolidado': linha['consolidado'],
        'valor_manutencao': linha['valor_manutencao'],
        'valor_disposicao': linha['valor_disposicao'],
        'valor_total': linha['valor_total'],
        'apontamentos': medicao.apontamentos.select_related('motivo_parada', 'obra_do_dia').order_by('data'),
        'ajustes': medicao.ajustes_admin.select_related('obra').order_by('obra__nome'),
        'data_emissao': date.today(),
        'empresa': {**EMPRESA, 'logo': _logo_data_uri()},
    }

    html = render_to_string('medicao_equip_boletim_pdf.html', contexto)
    response = HttpResponse(content_type='application/pdf')
    equip_slug = slugify(medicao.equipamento.prefixo)
    obra_slug = slugify(medicao.obra.nome) if medicao.obra_id else 'ceq'
    nome_arquivo = f"boletim_medicao_equip_{equip_slug}_{obra_slug}_{medicao.periodo.mes:02d}_{medicao.periodo.ano}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    return response


@login_required(login_url='/auth/login/')
def medicao_equip_ceq_resumo_pdf(request, periodo_id):
    if not (request.user.is_superuser or request.user.status == 'c'):
        return HttpResponse('<h1>Acesso negado</h1>')

    periodo = get_object_or_404(PeriodoMedicaoEquipamento, id=periodo_id)
    linhas = [servicos.linha_painel(m) for m in servicos.medicoes_do_periodo(periodo)]
    resumo = servicos.resumo_financeiro(linhas)

    contexto = {
        'periodo': periodo, 'linhas': linhas, 'resumo': resumo,
        'data_emissao': date.today(),
        'empresa': {**EMPRESA, 'logo': _logo_data_uri()},
    }

    html = render_to_string('medicao_equip_ceq_resumo_pdf.html', contexto)
    response = HttpResponse(content_type='application/pdf')
    nome_arquivo = f"resumo_medicao_equipamentos_{periodo.mes:02d}_{periodo.ano}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    return response
