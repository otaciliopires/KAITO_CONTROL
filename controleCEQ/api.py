from ninja import NinjaAPI
from .models import Abastecimento
from ativos.models import Equipamentos, Obras
from .schemas import AbastecimentoSchema, EquipamentosSchema, ObrasSchema

api= NinjaAPI()

@api.get("equipamentos/", response=list[EquipamentosSchema])
def get_equipamentos(request):
    return Equipamentos.objects.all()

@api.get("obras/", response=list[ObrasSchema])
def get_obras(request):
    return Obras.objects.all()

@api.get("abastecimento/", response=list[AbastecimentoSchema])
def get_abastecimentos(request):
    return Abastecimento.objects.all()    

