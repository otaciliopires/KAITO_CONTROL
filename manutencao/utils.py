from datetime import datetime, timezone, timedelta
from manutencao.models import Ordem_Oficina, Servico_Oficina
from django.db.models import Max


#gerar o NOW para importar nos views

now = datetime.now(timezone.utc)

def hora_correta(date_init, date_end):

      #função para calcular a hora correta de tempo aguardando serviço e tempo aguardando peças.
      #Calcula-se a diferença entre dois datetimes, e leva em consideração o dia de 9h para diferentes situações
      #CASO 3: hora_init>hora_end e dia_init<dia_end
      #CASO 1: hora init < hora end e datas init e end iguais
      #CASO2: horas init < hora end e dia init < dia end
      date_init = date_init - timedelta(hours=3) #ajustado as 3 horas de diferença para object.datetime type
      date_init = date_init.replace(tzinfo=None) #retirado o timezone. Necessário, pois se permanecesse, as 3 horas eram contabilizadas
      date_end = date_end.replace(tzinfo=None)
      #Quantidade de sábados e domingos
      days_list=[]
      current_date = date_init
      while current_date <= date_end:
            days_list.append(current_date.weekday())
            current_date += timedelta(days=1)
      saturdays = days_list.count(5)
      sundays = days_list.count(6)

      minute_init = date_init.minute
      hour_init= date_init.hour
      day_init = date_init.day
      month_init = date_init.month
      minute_end = date_end.minute
      hour_end = date_end.hour
      day_end = date_end.day
      month_end = date_end.month
      print("inicial",day_init,hour_init, date_init)
      print("final",day_end, hour_end, date_end)
      date_init = date_init.timestamp()
      date_end = date_end.timestamp()
      print((date_end-date_init)/3600)
      calculated_time = 0

      if hour_init <= hour_end and day_init == day_end and month_init == month_end:
            calculated_time = (date_end - date_init)/3600
            print('caso1')
      
      elif hour_init <= hour_end and day_init < day_end:
            if hour_end > 12 and hour_init < 12:      
                  calculated_time = (day_end - day_init)*9 + ((hour_end + minute_end*0.01666666667) - (hour_init + minute_end*0.01666666667)) -1 - saturdays*9 - sundays*9
            else:
                  calculated_time = (day_end - day_init)*9 + ((hour_end + minute_end*0.01666666667) - (hour_init + minute_end*0.01666666667))- saturdays*9 - sundays*9

                  print('caso2')

      elif hour_init > hour_end and day_init < day_end:
            if hour_init < 12 or hour_end > 12:
                  calculated_time = (hour_end + minute_end*0.01666666667 - 7) + (17 - hour_init + minute_init*0.01666666667) + (day_end - day_init - 1)*9 -1 - saturdays*9 - sundays*9
            else:
                  calculated_time = (hour_end + minute_end*0.01666666667 - 7) + (17 - hour_init + minute_init*0.01666666667) + (day_end - day_init - 1)*9 - saturdays*9 - sundays*9

            print('caso3')
      
      return calculated_time

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
            

def att_tempo_1_os(id, data_status):
      os_aberta = Ordem_Oficina.objects.get(id=id)
      servicos = Servico_Oficina.objects.filter(ordem_servico=os_aberta.id)
      print("testeerroda porra", data_status,os_aberta.data_status)
      print(data_status.replace(tzinfo=None),os_aberta.data_status.replace(tzinfo=None)- timedelta(hours=3) , "adasdasdasdnsdjfndksfjsdknsdkjn" )
      if data_status.replace(tzinfo=None) < os_aberta.data_status.replace(tzinfo=None) - timedelta(hours=3) :
            pass
      else:
            for servico in servicos:
                  if Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status="Em Serviço").exists():
                        os_aberta.tempo_em_servico = os_aberta.tempo_em_servico + (data_status.timestamp() - os_aberta.data_status.timestamp())/3600
                        os_aberta.tempo_total += (data_status.timestamp() - os_aberta.data_status.timestamp())/3600
                        servico.data_mudanca_status = data_status
                        os_aberta.data_status = data_status
                        os_aberta.status = "Em Serviço"
                        os_aberta.save()
                        print(os_aberta.status)
                        break
                  elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Peças').exists():
                        os_aberta.tempo_aguardo_peca = os_aberta.tempo_aguardo_peca + hora_correta(os_aberta.data_status, data_status)
                        os_aberta.tempo_total += hora_correta(os_aberta.data_status, data_status)
                        servico.data_mudanca_status = data_status
                        os_aberta.data_status = data_status
                        os_aberta.status = "Aguardando Peças"
                        os_aberta.save()
                        print(os_aberta.status)
                        break
                  elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Serviço').exists():
                        os_aberta.tempo_aguardo_servico = os_aberta.tempo_aguardo_servico + hora_correta(os_aberta.data_status, data_status)
                        os_aberta.tempo_total +=  hora_correta(os_aberta.data_status, data_status)
                        servico.data_mudanca_status =data_status
                        os_aberta.data_status = data_status
                        os_aberta.status = "Aguardando Serviço"
                        os_aberta.save()
                        print(os_aberta.status)
                        break

            
def att_tempo_2():
        os_oficina_abertas = Ordem_Oficina.objects.filter(data_fim=None)
        for os_aberta in os_oficina_abertas:
            servicos = Servico_Oficina.objects.filter(ordem_servico=os_aberta.id)
            if servicos.exists(): #verifica se a ordem tem algum serviço cadastrado
                for servico in servicos:
                        if Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status="Em Serviço").exists():
                               os_aberta.tempo_em_servico = os_aberta.tempo_em_servico + (servico.data_mudanca_status.timestamp() - os_aberta.data_status.timestamp())/3600
                               os_aberta.data_status = now
                               servico.data_mudanca_status = now                              
                               os_aberta.save()
                               break
                        elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Peças').exists():
                               os_aberta.tempo_aguardo_peca = os_aberta.tempo_aguardo_peca + (servico.data_mudanca_status.timestamp() - os_aberta.data_status.timestamp())/3600
                               os_aberta.data_status = now
                               servico.data_mudanca_status = now
                               os_aberta.save()
                               break
                        elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Serviço').exists():
                               os_aberta.tempo_aguardo_servico = os_aberta.tempo_aguardo_servico + (servico.data_mudanca_status.timestamp() - os_aberta.data_status.timestamp())/3600
                               os_aberta.data_status = now
                               servico.data_mudanca_status = now
                               os_aberta.save()
                               break
            else:pass
        return None
                
                    

def att_tempo_1_servico(id, data_status):
      data_status = datetime.strptime(data_status, "%Y-%m-%dT%H:%M")
      servico = Servico_Oficina.objects.get(id=id)
      print(servico.data_mudanca_status, servico.tempo_aguardo_peca, servico.tempo_aguardo_servico, servico.tempo_em_servico)

      if servico.status == "Em Serviço":
            print("testserv",servico.status, (data_status.timestamp() - servico.data_mudanca_status.timestamp())/3600)
            servico.tempo_em_servico = servico.tempo_em_servico + (data_status.timestamp() - servico.data_mudanca_status.timestamp())/3600
            servico.data_mudanca_status = data_status
            try:
                  servico.save()
                  print('deu certo')
            except:
                  print('deu errado')
      elif servico.status == "Aguardando Peças":
            print("testeap",servico.status, (now.timestamp() - servico.data_mudanca_status.timestamp())/3600)
            servico.tempo_aguardo_peca= servico.tempo_aguardo_peca + (data_status.timestamp() - servico.data_mudanca_status.timestamp())/3600
            servico.data_mudanca_status = data_status
            try:
                  servico.save()
                  print('deu certo')
            except:
                  print('deu errado')
            print("X",servico.data_mudanca_status)
      elif servico.status == 'Aguardando Serviço':
            print("testeas",servico.status, (now.timestamp() - servico.data_mudanca_status.timestamp())/3600)
            servico.tempo_aguardo_servico = servico.tempo_aguardo_servico + (data_status.timestamp() - servico.data_mudanca_status.timestamp())/3600
            servico.data_mudanca_status = data_status
            try:
                  servico.save()
                  print('deu certo')
            except:
                  print('deu errado')
            print("X",servico.data_mudanca_status)