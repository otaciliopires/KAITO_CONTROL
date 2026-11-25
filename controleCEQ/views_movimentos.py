"""Read-only lists, cascading choices and matching PDF exports."""
from datetime import date
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from ativos.models import Obras
from .models import Entrada, Transferencia, Tanque
from .views_saidas import ids_selecionados, chave_nome, tem_acesso
from .relatorios_pdf import n
from .movimentos_pdf import gerar_pdf

CONFIG = {
    'entradas': {'titulo':'Entradas','descricao':'Consulte as notas de diesel por período, obra e tanque.',
        'modelo':Entrada,'data':'data_entrega','quantidade':'quantidade','ordem':('-numero','-pk'),
        'primario':('obra','Obras',Obras,'nome','obra_id'),
        'secundario':('tanque','Tanques',Tanque,'prefixo','tanque_id'),
        'related':('obra','tanque','colaborador'),
        'cabecalho':['Nº','Tanque','Entrega','Emissão NF','Nota fiscal','Fornecedor','Obra','Quantidade (L)','Valor / L (R$)','Total (R$)','Colaborador','Observações'],
        'pdf_indices':[0,2,1,4,6,5,7,8,9],
        'pdf_larguras':[.055,.09,.09,.085,.20,.17,.105,.10,.105]},
    'transferencias': {'titulo':'Transferências','descricao':'Consulte as movimentações de diesel entre tanques e comboios.',
        'modelo':Transferencia,'data':'data','quantidade':'litros','ordem':('-data','-pk'),
        'primario':('tanque_fixo','Origens',Tanque,'prefixo','fixo_id'),
        'secundario':('tanque_movel','Destinos',Tanque,'prefixo','movel_id'),
        'related':('fixo','movel','colaborador'),
        'cabecalho':['Nº','Data','Origem','Destino','Quantidade (L)','Contador inicial','Contador final','Totalizador comboio','Colaborador'],
        'pdf_indices':list(range(9)), 'pdf_larguras':[.055,.09,.13,.13,.12,.11,.11,.12,.135]},
}


def opcoes(qs, spec):
    nome,rotulo,model,campo,fk=spec
    itens=model.objects.filter(pk__in=qs.order_by().values(fk))
    return [{'id':i.pk,'label':str(getattr(i,campo))} for i in sorted(itens,key=lambda i:(chave_nome(str(getattr(i,campo))),i.pk))]


def consultar(params,tipo,para_opcoes=False):
    cfg=CONFIG[tipo]
    raw_inicio=params.get('data_inicio') or params.get('data_inicio1') or params.get('data') or ''
    raw_fim=params.get('data_fim') or params.get('data_fim1') or ''
    try:
        inicio=date.fromisoformat(raw_inicio) if raw_inicio else None
        fim=date.fromisoformat(raw_fim) if raw_fim else None
    except ValueError:
        raise ValueError('Informe datas válidas para o período.')
    if inicio and fim and inicio>fim:
        raise ValueError('A data inicial deve ser anterior ou igual à final.')
    primeiro,segundo=cfg['primario'][0],cfg['secundario'][0]
    selecao1=ids_selecionados(params,primeiro)
    selecao2=ids_selecionados(params,segundo)
    base=cfg['modelo'].objects.all()
    if inicio: base=base.filter(**{cfg['data']+'__gte':inicio})
    if fim: base=base.filter(**{cfg['data']+'__lte':fim})
    opts1=opcoes(base,cfg['primario'])
    aplicados1=[i for i in selecao1 if i in {str(o['id']) for o in opts1}] if para_opcoes else selecao1
    recorte=base.filter(**{cfg['primario'][4]+'__in':aplicados1}) if aplicados1 else base
    opts2=opcoes(recorte,cfg['secundario'])
    qs=recorte.filter(**{cfg['secundario'][4]+'__in':selecao2}) if selecao2 else recorte
    qs=qs.select_related(*cfg['related']).order_by(*cfg['ordem'])
    pares=[]
    if inicio: pares.append(('data_inicio',inicio.isoformat()))
    if fim: pares.append(('data_fim',fim.isoformat()))
    pares.extend((primeiro,i) for i in selecao1)
    pares.extend((segundo,i) for i in selecao2)
    grupos=[]
    for spec,opts,selected in [(cfg['primario'],opts1,selecao1),(cfg['secundario'],opts2,selecao2)]:
        grupos.append({'nome':spec[0],'rotulo':spec[1],'opcoes':opts,'selecionados':selected})
    aviso=any(set(g['selecionados'])-{str(o['id']) for o in g['opcoes']} for g in grupos)
    return {'qs':qs,'inicio':inicio,'fim':fim,'grupos':grupos,'querystring':urlencode(pares),'aviso':aviso}


def celulas(r,tipo):
    if tipo=='entradas':
        return [r.numero,str(r.tanque),r.data_entrega.strftime('%d/%m/%Y'),r.data_nf.strftime('%d/%m/%Y'),
            r.nota_fiscal,r.fornecedor,str(r.obra),n(r.quantidade),n(r.preco_unitario,4),n(r.preco_total),
            r.colaborador.username if r.colaborador else '-',r.descricao or '-']
    return [r.pk,r.data.strftime('%d/%m/%Y'),str(r.fixo) if r.fixo else '-',str(r.movel) if r.movel else '-',
        n(r.litros),n(r.contador_inicio),n(r.contador_fim),n(r.contador_comboio),r.colaborador.username]


def lista(request,tipo):
    if not tem_acesso(request.user): return HttpResponseForbidden('Acesso negado.')
    params=request.POST if request.method=='POST' else request.GET
    cfg=CONFIG[tipo]
    erro=''
    try:
        dados=consultar(params,tipo)
    except ValueError as exc:
        erro=str(exc)
        dados={'qs':cfg['modelo'].objects.none(),'inicio':None,'fim':None,'grupos':[], 'querystring':'','aviso':False}
        for spec in (cfg['primario'],cfg['secundario']):
            dados['grupos'].append({'nome':spec[0],'rotulo':spec[1],'opcoes':[],'selecionados':[]})
    total=dados['qs'].aggregate(q=Sum(cfg['quantidade']))['q'] or 0
    valor=dados['qs'].aggregate(v=Sum('preco_total'))['v'] or 0 if tipo=='entradas' else None
    pagina=Paginator(dados['qs'],100).get_page(request.GET.get('page'))
    contexto=dict(dados,tipo=tipo,titulo=cfg['titulo'],descricao=cfg['descricao'],pagina=pagina,
        linhas=[celulas(r,tipo) for r in pagina],cabecalho=cfg['cabecalho'],total=total,valor=valor,erro=erro,
        data_inicio_raw=params.get('data_inicio',params.get('data','')),data_fim_raw=params.get('data_fim',''),
        obra_user=Obras.objects.filter(usuario=request.user))
    contexto[tipo]=pagina
    return render(request,'movimentos/lista.html',contexto,status=400 if erro else 200)


def choices(request,tipo):
    if not tem_acesso(request.user): return JsonResponse({'erro':'Acesso negado.'},status=403)
    try:
        dados=consultar(request.GET,tipo,para_opcoes=True)
    except ValueError as exc:
        return JsonResponse({'erro':str(exc)},status=400)
    return JsonResponse({'grupos':{g['nome']:g['opcoes'] for g in dados['grupos']}})


def pdf(request,tipo):
    if not tem_acesso(request.user): return HttpResponseForbidden('Acesso negado.')
    try:
        dados=consultar(request.GET,tipo)
    except ValueError as exc:
        return HttpResponse(str(exc),status=400)
    cfg=CONFIG[tipo]
    registros=list(dados['qs'])
    conteudo=gerar_pdf(tipo,cfg,dados,registros,celulas,timezone.localtime())
    response=HttpResponse(conteudo,content_type='application/pdf')
    response['Content-Disposition']='inline; filename="'+tipo+'-diesel.pdf"'
    return response


@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def entradas(request): return lista(request,'entradas')

@login_required(login_url='/auth/login/')
@never_cache
def transferencias(request): return lista(request,'transferencias')

@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def entradas_opcoes(request): return choices(request,'entradas')

@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def transferencias_opcoes(request): return choices(request,'transferencias')

@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def entradas_pdf(request): return pdf(request,'entradas')

@login_required(login_url='/auth/login/')
@require_GET
@never_cache
def transferencias_pdf(request): return pdf(request,'transferencias')
