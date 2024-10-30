from ninja import ModelSchema, Schema
from .models import Abastecimento
from ativos.models import Equipamentos, Obras


class EquipamentosSchema(ModelSchema):
    class Meta:
        model = Equipamentos
        fields = ('prefixo',)

class ObrasSchema(ModelSchema):
    class Meta:
        model = Obras
        fields = ('nome','saldo')

class AbastecimentoSchema(ModelSchema):
    equipamento: EquipamentosSchema | None=None
    obra: ObrasSchema | None=None

    class Meta:
        model = Abastecimento
        fields = ('data','obra','equipamento', 'litros')

