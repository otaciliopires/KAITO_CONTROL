"""Read-only monthly history, with an independent range for each work site."""
from datetime import date
from decimal import Decimal
from urllib.parse import urlencode
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.urls import reverse
from django.utils import timezone
from ativos.models import Obras
from .models import Entrada, Abastecimento
from .views_relatorios import MESES, chave_nome, numero

ZERO = Decimal('0')


def proximo_mes(dia):
    return date(dia.year+1,1,1) if dia.month==12 else date(dia.year,dia.month+1,1)


def dados_historico(request):
    obras=sorted(Obras.objects.all(),key=lambda o:(chave_nome(o.nome),o.pk))
    raw=request.GET.get('obra','').strip()
    selecionada=next((o for o in obras if str(o.pk)==raw),None) if raw else None
    aviso='Obra não encontrada. Selecione uma obra válida.' if raw and selecionada is None else ''
    escolhidas=[selecionada] if selecionada else ([] if aviso else obras)
    entradas=Entrada.objects.all()
    saidas=Abastecimento.objects.exclude(obra_id=None)
    if raw:
        entradas=entradas.filter(obra=selecionada) if selecionada else entradas.none()
        saidas=saidas.filter(obra=selecionada) if selecionada else saidas.none()
    grupos={o.pk:{} for o in escolhidas}
    for campo,qs,data_campo,quantidade in [('entradas',entradas,'data_entrega','quantidade'),('saidas',saidas,'data','litros')]:
        agregado=qs.order_by().annotate(mes=TruncMonth(data_campo)).values('obra_id','mes').annotate(total=Sum(quantidade),registros=Count('pk'))
        for row in agregado:
            if row['obra_id'] not in grupos: continue
            mes=row['mes']
            if mes is None: continue
            valor=grupos[row['obra_id']].setdefault(mes,{'entradas':ZERO,'saidas':ZERO,'notas':0,'registros':0})
            valor[campo]=numero(row['total'])
            valor['notas' if campo=='entradas' else 'registros']=row['registros']
    historicos=[]
    sem_movimento=[]
    resumo={'entradas':ZERO,'saidas':ZERO,'resultado':ZERO,'notas':0,'registros':0}
    for obra in escolhidas:
        meses=grupos[obra.pk]
        if not meses:
            sem_movimento.append(obra)
            continue
        inicio,fim=min(meses),max(meses)
        atual=inicio
        acumulado=ZERO
        linhas=[]
        totais={'entradas':ZERO,'saidas':ZERO,'notas':0,'registros':0}
        while atual<=fim:
            valores=meses.get(atual,{'entradas':ZERO,'saidas':ZERO,'notas':0,'registros':0})
            resultado=valores['entradas']-valores['saidas']
            acumulado+=resultado
            linhas.append(dict(valores,mes=atual,rotulo=MESES[atual.month-1]+' / '+str(atual.year),
                resultado=resultado,acumulado=acumulado,sem_movimento=not(valores['notas'] or valores['registros'])))
            for key in totais: totais[key]+=valores[key]
            if atual==fim: break
            atual=proximo_mes(atual)
        totais['resultado']=acumulado
        historicos.append({'obra':obra,'inicio':inicio,'fim':fim,'linhas':linhas,'totais':totais,'meses':len(linhas)})
        for key in resumo: resumo[key]+=totais[key]
    primeiro=min((h['inicio'] for h in historicos),default=None)
    ultimo=max((h['fim'] for h in historicos),default=None)
    params={'visao':'historico'}
    if raw: params['obra']=raw
    sem_obra=Abastecimento.objects.filter(obra_id=None).aggregate(total=Sum('litros'),registros=Count('pk')) if not raw else {'total':ZERO,'registros':0}
    return {'visao':'historico','obras':obras,'obra_selecionada':selecionada,'historicos':historicos,
        'obras_sem_movimento':sem_movimento,'resumo':resumo,'primeiro_mes':primeiro,'ultimo_mes':ultimo,
        'aviso':aviso,'sem_obra':sem_obra,'gerado_em':timezone.localtime(),
        'pdf_link':reverse('relatorio_pdf')+'?'+urlencode(params),
        'mensal_link':reverse('relatorio')+'?visao=mensal',
        'obra_link':reverse('relatorio')+'?'+urlencode({'visao':'obra',**({'obra':selecionada.pk} if selecionada else {})}),
        'historico_link':reverse('relatorio')+'?visao=historico'}
