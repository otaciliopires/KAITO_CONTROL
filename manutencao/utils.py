from datetime import datetime, timezone
from manutencao.models import Ordem_Oficina, Servico_Oficina
from django.db.models import Max

#gerar o NOW para importar nos views

now = datetime.now(timezone.utc)

#atualização na página de OS e na de serviço
def att_tempo(data_status, id_os_atual):
        os_oficina_aberta = Ordem_Oficina.objects.filter(data_fim=None)
        for os_aberta in os_oficina_aberta:
            servicos_oficina = Servico_Oficina.objects.filter(ordem_servico=os_aberta.id)
            # if os_aberta.id == id_os_atual:
            for servico in servicos_oficina:
                    if servico.status == 'Em Serviço':
                        x = os_aberta.tempo_em_servico + (now.timestamp()-data_status.timestamp())/3600   
                        # os_aberta.data_status = data_status 
                        data_recente = Servico_Oficina.objects.filter(data_fim=None, ordem_servico=os_aberta).aggregate(Max('data_mudanca_status'))['data_mudanca_status__max']
                        print(x)
                        pass
            # else:

                    return None
            

def att_tempo_1(id, data_status):
      data_status = datetime.strptime(data_status, "%Y-%m-%dT%H:%M")
      os_aberta = Ordem_Oficina.objects.get(id=id)
      if os_aberta.data_status.timestamp() > data_status.timestamp():
            data_status = os_aberta.data_status
      servicos = Servico_Oficina.objects.filter(ordem_servico=os_aberta.id)
      for servico in servicos:
            if Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status="Em Serviço").exists():
                  os_aberta.tempo_em_servico = os_aberta.tempo_em_servico + (data_status.timestamp() - os_aberta.data_status.timestamp())/3600
                  servico.data_mudanca_status = data_status
                  os_aberta.data_status = data_status
                  os_aberta.status = "Em Serviço"
                  os_aberta.save()
                  break
            elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Peças').exists():
                  os_aberta.tempo_aguardo_peca = os_aberta.tempo_aguardo_peca + (data_status.timestamp() - os_aberta.data_status.timestamp())/3600
                  servico.data_mudanca_status = data_status
                  os_aberta.data_status = data_status
                  os_aberta.status = "Aguardando Peças"
                  os_aberta.save()
                  break
            elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Serviço').exists():
                  os_aberta.tempo_aguardo_servico = os_aberta.tempo_aguardo_servico + (data_status.timestamp() - os_aberta.data_status.timestamp())/3600
                  servico.data_mudanca_status =data_status
                  os_aberta.data_status = data_status
                  os_aberta.status = "Aguardando Serviço"
                  os_aberta.save()
                  break


def att_tempo_2():
        os_oficina_abertas = Ordem_Oficina.objects.filter(data_fim=None)
        for os_aberta in os_oficina_abertas:
            servicos = Servico_Oficina.objects.filter(ordem_servico=os_aberta.id)
            if servicos.exists(): #verifica se a ordem tem algum serviço cadastrado
                for servico in servicos:
                        if Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status="Em Serviço").exists():
                               os_aberta.tempo_em_servico = os_aberta.tempo_em_servico + (now.timestamp() - os_aberta.data_status.timestamp())/3600
                               os_aberta.data_status = now
                               servico.data_mudanca_status = now                              
                               os_aberta.save()
                               break
                        elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Peças').exists():
                               os_aberta.tempo_aguardo_peca = os_aberta.tempo_aguardo_peca + (now.timestamp() - os_aberta.data_status.timestamp())/3600
                               os_aberta.data_status = now
                               servico.data_mudanca_status = now
                               os_aberta.save()
                               break
                        elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Serviço').exists():
                               os_aberta.tempo_aguardo_servico = os_aberta.tempo_aguardo_servico + (now.timestamp() - os_aberta.data_status.timestamp())/3600
                               os_aberta.data_status = now
                               servico.data_mudanca_status = now
                               os_aberta.save()
                               break
            else:pass
        return None
                
                    

                  
      