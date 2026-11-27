"""Shared column definitions for the outgoing list and PDF."""
COLUNAS = [
    {'id':'numero','titulo':'Nº','peso':.055},
    {'id':'tanque','titulo':'Tanque','peso':.065},
    {'id':'data','titulo':'Data','peso':.075},
    {'id':'obra','titulo':'Obra','peso':.15},
    {'id':'equipamento','titulo':'Equipamento','peso':.085},
    {'id':'descricao','titulo':'Descrição','peso':.14},
    {'id':'propriedade','titulo':'Propriedade','peso':.08},
    {'id':'quantidade','titulo':'Quantidade (L)','peso':.085},
    {'id':'horimetro','titulo':'Horímetro / km','peso':.085},
    {'id':'lubrificacao','titulo':'Lubrificação','peso':.08},
    {'id':'operador','titulo':'Operador / motorista','peso':.13},
]


def selecionar_colunas(params):
    if 'coluna' not in params and params.get('personalizar_colunas')!='1':
        return list(COLUNAS)
    ids=set(params.getlist('coluna'))
    if not ids or ids-{c['id'] for c in COLUNAS}:
        raise ValueError('Selecione pelo menos uma coluna válida para o relatório.')
    return [c for c in COLUNAS if c['id'] in ids]
