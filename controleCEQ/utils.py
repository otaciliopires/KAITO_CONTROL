from .models import Entrada
import json
from django.db.models import Avg

def nonetest(value):
    if value == None:
        value = 0
    else:
        value = value
    return value



def grafico_vunit(year):


    label = json.dumps(['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'])

    avg_unit = []
    for month in range(1,13):
        avg_unit.append(nonetest(Entrada.objects.filter(data_entrega__month=month).filter(data_entrega__year=year).aggregate(Avg('preco_unitario'))['preco_unitario__avg']))
    avg_unit = json.dumps(avg_unit)
    
    
    return {'label':label, 'data':avg_unit}