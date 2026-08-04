from django.db import models
from autenticacao.models import Usuario
from ativos.models import Equipamentos


class Solicitacao(models.Model):
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitacoes_estoque')
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitacoes_estoque')
    observacao = models.TextField(blank=True, default="")
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solicitação #{self.id} - {self.solicitante}"


class ItemSolicitacao(models.Model):
    tipo_status = (
        ("SOL", "Solicitado"),
        ("COM", "Comprado"),
        ("REC", "Recebido"),
        ("RET", "Retirado"),
    )

    solicitacao = models.ForeignKey(Solicitacao, on_delete=models.CASCADE, related_name='itens')
    descricao = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField(default=1)
    imagem = models.ImageField(upload_to='estoque/solicitacoes/', blank=True, null=True)
    status = models.CharField(max_length=3, choices=tipo_status, default="SOL")

    # etapa comprador
    referencia = models.CharField(max_length=50, blank=True, default="")
    fornecedor = models.CharField(max_length=100, blank=True, default="")
    nota_fiscal = models.CharField(max_length=30, blank=True, default="")
    preco_unitario = models.FloatField(null=True, blank=True)
    preco_total = models.FloatField(null=True, blank=True)
    comprador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_comprados')
    data_compra = models.DateTimeField(null=True, blank=True)

    # etapa almoxarifado
    local_estoque = models.CharField(max_length=50, blank=True, default="")
    almoxarifado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_recebidos')
    data_recebimento = models.DateTimeField(null=True, blank=True)

    # etapa retirada
    retirado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_retirados')
    data_retirada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.descricao} ({self.get_status_display()})"


class EntradaEstoque(models.Model):
    peca = models.CharField(max_length=150)
    referencia = models.CharField(max_length=50, blank=True, default="")
    fornecedor = models.CharField(max_length=100, blank=True, default="")
    nota_fiscal = models.CharField(max_length=30, blank=True, default="")
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.FloatField()
    preco_total = models.FloatField()
    local_estoque = models.CharField(max_length=50)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    data_entrada = models.DateTimeField(auto_now_add=True)
    item_solicitacao = models.ForeignKey(ItemSolicitacao, on_delete=models.SET_NULL, null=True, blank=True, related_name='entradas')

    def __str__(self):
        return f"{self.peca} - {self.quantidade} un"
