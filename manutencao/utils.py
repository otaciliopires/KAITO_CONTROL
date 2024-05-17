from datetime import datetime, timezone
from manutencao.models import Ordem_Oficina, Servico_Oficina


#gerar o NOW para importar nos views

now = datetime.now(timezone.utc)


def att_tempo(data_status):


    return None