from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Solicitacao, ItemSolicitacao, EntradaEstoque
from ativos.models import Equipamentos
from autenticacao.models import Usuario


def _tem_permissao(user, perfil):
    return user.is_superuser or user.perfil_estoque == perfil


@login_required(login_url='/auth/login/')
def estoque_home(request):
    return render(request, 'estoque_home.html')


@login_required(login_url='/auth/login/')
def nova_solicitacao(request):
    if not _tem_permissao(request.user, 'solicitante'):
        return HttpResponse('<h1>Acesso negado</h1>')

    equipamentos = Equipamentos.objects.all()

    if request.method == 'POST':
        equipamento_id = request.POST.get('equipamento') or None
        observacao = request.POST.get('observacao', '')

        solicitacao = Solicitacao.objects.create(
            solicitante=request.user,
            equipamento_id=equipamento_id,
            observacao=observacao,
        )

        total_itens = int(request.POST.get('total_itens', 0) or 0)
        criou_algum_item = False
        for i in range(total_itens):
            descricao = request.POST.get(f'descricao_{i}', '').strip()
            if not descricao:
                continue
            quantidade = request.POST.get(f'quantidade_{i}') or 1
            imagem = request.FILES.get(f'imagem_{i}')
            ItemSolicitacao.objects.create(
                solicitacao=solicitacao,
                descricao=descricao,
                quantidade=quantidade,
                imagem=imagem,
            )
            criou_algum_item = True

        if not criou_algum_item:
            solicitacao.delete()
            return render(request, 'estoque_nova_solicitacao.html', {
                'equipamentos': equipamentos,
                'erro': 'Adicione ao menos um item com descrição.',
            })

        return redirect('minhas_solicitacoes')

    return render(request, 'estoque_nova_solicitacao.html', {'equipamentos': equipamentos})


@login_required(login_url='/auth/login/')
def minhas_solicitacoes(request):
    solicitacoes_qs = Solicitacao.objects.filter(solicitante=request.user).order_by('-data_solicitacao').prefetch_related('itens')
    paginator = Paginator(solicitacoes_qs, 50)
    solicitacoes = paginator.get_page(request.GET.get('page'))
    return render(request, 'estoque_minhas_solicitacoes.html', {'solicitacoes': solicitacoes})


@login_required(login_url='/auth/login/')
def comprar_lista(request):
    if not _tem_permissao(request.user, 'comprador'):
        return HttpResponse('<h1>Acesso negado</h1>')
    itens = ItemSolicitacao.objects.filter(status='SOL').order_by('solicitacao__data_solicitacao')
    return render(request, 'estoque_comprar.html', {'itens': itens})


@login_required(login_url='/auth/login/')
def comprar_item(request, item_id):
    if not _tem_permissao(request.user, 'comprador'):
        return HttpResponse('<h1>Acesso negado</h1>')
    item = get_object_or_404(ItemSolicitacao, id=item_id)
    if request.method == 'POST':
        item.referencia = request.POST.get('referencia', '')
        item.fornecedor = request.POST.get('fornecedor', '')
        item.nota_fiscal = request.POST.get('nota_fiscal', '')
        item.preco_unitario = request.POST.get('preco_unitario') or None
        item.preco_total = request.POST.get('preco_total') or None
        item.comprador = request.user
        item.data_compra = timezone.now()
        item.status = 'COM'
        item.save()
    return redirect('comprar_lista')


@login_required(login_url='/auth/login/')
def receber_lista(request):
    if not _tem_permissao(request.user, 'almoxarifado'):
        return HttpResponse('<h1>Acesso negado</h1>')
    aguardando_recebimento = ItemSolicitacao.objects.filter(status='COM').order_by('data_compra')
    aguardando_retirada = ItemSolicitacao.objects.filter(status='REC').order_by('data_recebimento')
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'estoque_receber.html', {
        'aguardando_recebimento': aguardando_recebimento,
        'aguardando_retirada': aguardando_retirada,
        'usuarios': usuarios,
    })


@login_required(login_url='/auth/login/')
def receber_item(request, item_id):
    if not _tem_permissao(request.user, 'almoxarifado'):
        return HttpResponse('<h1>Acesso negado</h1>')
    item = get_object_or_404(ItemSolicitacao, id=item_id)
    if request.method == 'POST':
        local_estoque = request.POST.get('local_estoque', '')
        item.local_estoque = local_estoque
        item.almoxarifado = request.user
        item.data_recebimento = timezone.now()
        item.status = 'REC'
        item.save()

        EntradaEstoque.objects.create(
            peca=item.descricao,
            referencia=item.referencia,
            fornecedor=item.fornecedor,
            nota_fiscal=item.nota_fiscal,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario or 0,
            preco_total=item.preco_total or 0,
            local_estoque=local_estoque,
            usuario=request.user,
            item_solicitacao=item,
        )
    return redirect('receber_lista')


@login_required(login_url='/auth/login/')
def retirar_item(request, item_id):
    if not _tem_permissao(request.user, 'almoxarifado'):
        return HttpResponse('<h1>Acesso negado</h1>')
    item = get_object_or_404(ItemSolicitacao, id=item_id)
    if request.method == 'POST':
        retirado_por_id = request.POST.get('retirado_por') or item.solicitacao.solicitante_id
        item.retirado_por_id = retirado_por_id
        item.data_retirada = timezone.now()
        item.status = 'RET'
        item.save()
    return redirect('receber_lista')


@login_required(login_url='/auth/login/')
def dar_entrada(request):
    if not _tem_permissao(request.user, 'almoxarifado'):
        return HttpResponse('<h1>Acesso negado</h1>')
    if request.method == 'POST':
        peca = request.POST.get('peca', '')
        referencia = request.POST.get('referencia', '')
        fornecedor = request.POST.get('fornecedor', '')
        nota_fiscal = request.POST.get('nota_fiscal', '')
        quantidade = request.POST.get('quantidade') or 1
        preco_unitario = request.POST.get('preco_unitario') or 0
        preco_total = request.POST.get('preco_total') or 0
        local_estoque = request.POST.get('local_estoque', '')

        EntradaEstoque.objects.create(
            peca=peca,
            referencia=referencia,
            fornecedor=fornecedor,
            nota_fiscal=nota_fiscal,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            preco_total=preco_total,
            local_estoque=local_estoque,
            usuario=request.user,
        )
        return redirect('dar_entrada')

    entradas = EntradaEstoque.objects.order_by('-data_entrada')[:50]
    return render(request, 'estoque_dar_entrada.html', {'entradas': entradas})


@login_required(login_url='/auth/login/')
def fluxo(request):
    itens = ItemSolicitacao.objects.select_related('solicitacao', 'solicitacao__solicitante', 'solicitacao__equipamento').order_by('-solicitacao__data_solicitacao')
    colunas = {'SOL': [], 'COM': [], 'REC': [], 'RET': []}
    for item in itens:
        colunas[item.status].append(item)

    return render(request, 'estoque_fluxo.html', {'colunas': colunas})
