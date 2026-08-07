import base64
from datetime import date
from functools import lru_cache

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Min
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from ativos.models import Obras
from .models import ContratoMedicaoCaminhao, FechamentoMedicaoCaminhao
from .services import (
    calcular_acumulado, calcular_periodo, meses_do_ano,
    MESES_PT, fim_mes, mes_encerrado,
)

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


@login_required(login_url='/auth/login/')
def medicao_obra_home(request, obra_id):
    obra = get_object_or_404(Obras, id=obra_id)
    return render(request, 'medicao_obra_home.html', {'obra': obra})


@login_required(login_url='/auth/login/')
def medicao_caminhao_lista(request, obra_id):
    obra = get_object_or_404(Obras, id=obra_id)
    contratos = (
        ContratoMedicaoCaminhao.objects.filter(obra=obra, ativo=True)
        .select_related('caminhao', 'caminhao__tanque')
    )

    if contratos.count() == 1:
        return redirect('medicao_meses', contrato_id=contratos.first().id)

    return render(request, 'medicao_caminhao_lista.html', {'obra': obra, 'contratos': contratos})


@login_required(login_url='/auth/login/')
def medicao_meses(request, contrato_id):
    contrato = get_object_or_404(
        ContratoMedicaoCaminhao.objects.select_related('obra', 'caminhao'), id=contrato_id
    )

    hoje = date.today()
    try:
        ano = int(request.GET.get('ano', hoje.year))
    except ValueError:
        ano = hoje.year

    ano_min = contrato.mes_referencia_inicial.year
    ano_max = hoje.year
    ano = max(ano_min, min(ano, ano_max))

    meses = meses_do_ano(contrato, ano)

    return render(request, 'medicao_meses.html', {
        'contrato': contrato,
        'obra': contrato.obra,
        'ano': ano,
        'ano_min': ano_min,
        'ano_max': ano_max,
        'meses': meses,
    })


def _carregar_contexto_relatorio(contrato_id, ano, mes):
    if mes < 1 or mes > 12:
        raise Http404('Mês inválido')

    contrato = get_object_or_404(
        ContratoMedicaoCaminhao.objects.select_related('obra', 'caminhao', 'caminhao__tanque'), id=contrato_id
    )
    inicio = contrato.mes_referencia_inicial
    if (ano, mes) < (inicio.year, inicio.month):
        raise Http404('Mês fora do período controlado pelo Kaito para este contrato.')

    acumulado = calcular_acumulado(contrato, ano, mes)
    fechamento = (
        FechamentoMedicaoCaminhao.objects
        .filter(contrato=contrato, ano=ano, mes=mes)
        .select_related('fechado_por')
        .first()
    )
    encerrado = mes_encerrado(ano, mes)

    return {
        'contrato': contrato,
        'obra': contrato.obra,
        'caminhao': contrato.caminhao,
        'ano': ano,
        'mes': mes,
        'nome_mes': MESES_PT[mes],
        'acumulado': acumulado,
        'periodo': acumulado.periodo,
        'fim_mes': fim_mes(ano, mes),
        'fechamento': fechamento,
        'fechado': fechamento is not None,
        'mes_encerrado': encerrado,
        'pode_fechar': encerrado and fechamento is None,
    }


@login_required(login_url='/auth/login/')
def medicao_relatorio(request, contrato_id, ano, mes):
    contexto = _carregar_contexto_relatorio(contrato_id, ano, mes)
    return render(request, 'medicao_relatorio.html', contexto)


@login_required(login_url='/auth/login/')
@require_POST
def medicao_fechar_mes(request, contrato_id, ano, mes):
    if mes < 1 or mes > 12:
        raise Http404('Mês inválido')

    contrato = get_object_or_404(ContratoMedicaoCaminhao, id=contrato_id)
    inicio = contrato.mes_referencia_inicial
    if (ano, mes) < (inicio.year, inicio.month):
        raise Http404('Mês fora do período controlado pelo Kaito para este contrato.')

    if request.user.status != 'c':
        messages.add_message(request, messages.WARNING, 'Só a Central de Equipamentos pode fechar a medição do mês.')
    elif not mes_encerrado(ano, mes):
        messages.add_message(request, messages.WARNING, 'Esse mês ainda não terminou, por isso não pode ser fechado.')
    else:
        _, criado = FechamentoMedicaoCaminhao.objects.get_or_create(
            contrato=contrato, ano=ano, mes=mes,
            defaults={'fechado_por': request.user},
        )
        if criado:
            messages.add_message(request, messages.SUCCESS, 'Mês fechado com sucesso. O boletim de medição já pode ser baixado.')
        else:
            messages.add_message(request, messages.INFO, 'Esse mês já estava fechado.')

    return redirect('medicao_relatorio', contrato_id=contrato_id, ano=ano, mes=mes)


@login_required(login_url='/auth/login/')
def medicao_boletim_pdf(request, contrato_id, ano, mes):
    contexto = _carregar_contexto_relatorio(contrato_id, ano, mes)

    if not contexto['fechado']:
        messages.add_message(request, messages.WARNING, 'Feche o mês antes de baixar o boletim de medição.')
        return redirect('medicao_relatorio', contrato_id=contrato_id, ano=ano, mes=mes)

    contexto['data_emissao'] = date.today()
    contexto['empresa'] = {**EMPRESA, 'logo': _logo_data_uri()}

    html = render_to_string('medicao_boletim_pdf.html', contexto)

    response = HttpResponse(content_type='application/pdf')
    obra_slug = slugify(contexto['obra'].nome)
    caminhao_slug = slugify(contexto['caminhao'].identificacao)
    nome_arquivo = f"boletim_medicao_{caminhao_slug}_{obra_slug}_{mes:02d}_{ano}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    return response


@login_required(login_url='/auth/login/')
def medicao_painel_ceq(request):
    if request.user.status != 'c':
        return HttpResponse('<h1>Acesso Negado</h1>')

    hoje = date.today()
    ano_mes_anterior, mes_anterior = (hoje.year, hoje.month - 1) if hoje.month > 1 else (hoje.year - 1, 12)

    try:
        ano_str, mes_str = request.GET.get('periodo', '').split('-')
        ano, mes = int(ano_str), int(mes_str)
        if mes < 1 or mes > 12:
            raise ValueError
    except (ValueError, AttributeError):
        ano, mes = ano_mes_anterior, mes_anterior

    if (ano, mes) > (hoje.year, hoje.month):
        ano, mes = hoje.year, hoje.month

    contratos = (
        ContratoMedicaoCaminhao.objects.filter(ativo=True)
        .select_related('obra', 'caminhao', 'caminhao__tanque')
        .order_by('obra__nome', 'caminhao__identificacao')
    )

    linhas = []
    valor_total_mes = 0.0

    for contrato in contratos:
        periodo = None
        if not (ano, mes) < (contrato.mes_referencia_inicial.year, contrato.mes_referencia_inicial.month):
            periodo = calcular_periodo(contrato, ano, mes, incluir_tabela=False)
            valor_total_mes += periodo.total

        linhas.append({
            'contrato': contrato,
            'periodo_atual': periodo,
        })

    inicio_min = contratos.aggregate(inicio=Min('mes_referencia_inicial'))['inicio'] or hoje
    opcoes_mes = []
    ano_it, mes_it = hoje.year, hoje.month
    while (ano_it, mes_it) >= (inicio_min.year, inicio_min.month):
        opcoes_mes.append({'ano': ano_it, 'mes': mes_it, 'nome': MESES_PT[mes_it]})
        ano_it, mes_it = (ano_it, mes_it - 1) if mes_it > 1 else (ano_it - 1, 12)

    return render(request, 'medicao_painel_ceq.html', {
        'linhas': linhas,
        'total_contratos': len(linhas),
        'total_obras': contratos.values('obra').distinct().count(),
        'valor_total_mes': valor_total_mes,
        'nome_mes_selecionado': MESES_PT[mes],
        'ano_selecionado': ano,
        'mes_selecionado': mes,
        'mes_em_andamento': (ano, mes) == (hoje.year, hoje.month),
        'opcoes_mes': opcoes_mes,
    })
