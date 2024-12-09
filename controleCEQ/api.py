from ninja import NinjaAPI
from .models import Abastecimento
from ativos.models import Equipamentos, Obras
from .schemas import AbastecimentoSchema, EquipamentosSchema, ObrasSchema
from typing import List

api= NinjaAPI()

@api.get("equipamentos/", response=List[EquipamentosSchema])
def get_equipamentos(request):
    return Equipamentos.objects.all()

@api.get("obras/", response=List[ObrasSchema])
def get_obras(request):
    return Obras.objects.all()

@api.get("abastecimento/", response=List[AbastecimentoSchema])
def get_abastecimentos(request):
    return Abastecimento.objects.all()    

