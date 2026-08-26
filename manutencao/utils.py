from datetime import timedelta
from manutencao.models import Ordem_Oficina, Servico_Oficina


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
      date_init = date_init.timestamp()
      date_end = date_end.timestamp()
      calculated_time = 0

      if hour_init <= hour_end and day_init == day_end and month_init == month_end:
            calculated_time = (date_end - date_init)/3600

      elif hour_init <= hour_end and day_init < day_end:
            if hour_end > 12 and hour_init < 12:
                  calculated_time = (day_end - day_init)*9 + ((hour_end + minute_end*0.01666666667) - (hour_init + minute_end*0.01666666667)) -1 - saturdays*9 - sundays*9
            else:
                  calculated_time = (day_end - day_init)*9 + ((hour_end + minute_end*0.01666666667) - (hour_init + minute_end*0.01666666667))- saturdays*9 - sundays*9

      elif hour_init > hour_end and day_init < day_end:
            if hour_init < 12 or hour_end > 12:
                  calculated_time = (hour_end + minute_end*0.01666666667 - 7) + (17 - hour_init + minute_init*0.01666666667) + (day_end - day_init - 1)*9 -1 - saturdays*9 - sundays*9
            else:
                  calculated_time = (hour_end + minute_end*0.01666666667 - 7) + (17 - hour_init + minute_init*0.01666666667) + (day_end - day_init - 1)*9 - saturdays*9 - sundays*9

      return calculated_time


def att_tempo_1_os(id, data_status):
      os_aberta = Ordem_Oficina.objects.get(id=id)
      servicos = Servico_Oficina.objects.filter(ordem_servico=os_aberta.id)
      if data_status.replace(tzinfo=None) < os_aberta.data_status.replace(tzinfo=None) - timedelta(hours=3):
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
                        break
                  elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Peças').exists():
                        os_aberta.tempo_aguardo_peca = os_aberta.tempo_aguardo_peca + hora_correta(os_aberta.data_status, data_status)
                        os_aberta.tempo_total += hora_correta(os_aberta.data_status, data_status)
                        servico.data_mudanca_status = data_status
                        os_aberta.data_status = data_status
                        os_aberta.status = "Aguardando Peças"
                        os_aberta.save()
                        break
                  elif Servico_Oficina.objects.filter(ordem_servico=os_aberta.id, status='Aguardando Serviço').exists():
                        os_aberta.tempo_aguardo_servico = os_aberta.tempo_aguardo_servico + hora_correta(os_aberta.data_status, data_status)
                        os_aberta.tempo_total +=  hora_correta(os_aberta.data_status, data_status)
                        servico.data_mudanca_status =data_status
                        os_aberta.data_status = data_status
                        os_aberta.status = "Aguardando Serviço"
                        os_aberta.save()
                        break