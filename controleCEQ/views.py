from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Abastecimento, Tanque, Transferencia, Entrada, Saldo
from ativos.models import Equipamentos, Obras
from autenticacao.models import Usuario
import datetime
from datetime import date, datetime
from django.db.models import Sum, Avg, Max
from . utils import nonetest, grafico_vunit
import openpyxl
import json
from operator import itemgetter
from django.contrib import messages
from django.contrib.messages import constants



""" Para filtrar uma ForeignKey foi necessário adquirir o valor.id do respectivo item. O filtro da ForeignKey requisita que você
faça isso. No value do formulário foi pedido o equipamento.id e a obra.id  --  em seguida, foi utilizado o 
filter(carateristica_objeto__in=lista_variável -- Em que a lista variável é uma lista de id que quer filtrar da ForeignKey"""


@login_required(login_url='/auth/login/')
def home(request):
    
    if request.method == 'GET' and request.user.status=='c':

        
        user = request.user
        obra_user=Obras.objects.filter(usuario=user.id)
        tanques = Tanque.objects.all()
        obras = Obras.objects.all()
        equipamentos = Equipamentos.objects.all()


        """Esse script serve para verificar dentro de um excel todos os equipamentos e cadastrá-los
        Utilizar esse código mas transformando o excel em um dictionary e cadastrando os dados do dict
        assim ficará masis fácil o cadastro dentro do servidor
        realizar uma verificação para se o equipamento já for cadastrado, não cadastrar mais"""
        # delete_all = Entrada.objects.all()
        # delete_all.delete()
        
        #Método para cadastrar os equipamentos

        # excel = "media/fotos/equipamentos2.xlsx"
        # workbooks = openpyxl.load_workbook(excel)
        # equipamentss = workbooks['Equipamentos']
        # total_list_x=[]
        # list_x = []
        # for i in equipamentss.iter_rows(min_row=2,values_only=True):
        #         equip = i[:4]
        #         print(equip)
        #         if equip[0] == None:
        #                 break
        #         else:
        #             total_list_x.append(equip) 
        # for i in total_list_x:
        #     print(i[3]) 

        lista_equipamentos = [('TT-01', 'TESTE', 'CONTRUTORA ROCHA', 'R')]
        # ('AB-01', 'AUTOBETONEIRA', 'CONSTRUTORA ROCHA', 'R')
        # ('AGI-4972', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('AGX-4C19', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('AHN-2E69', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('ALMOXARIFADO', 'RESERVATÓRIO DE DIESEL PRESENTE NA OBRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('BHP-2199', 'CAÇAMBA TERCEIRIZADA', 'JOSÉ VAMBERTO BASTOS VIEIRA', 'T'),
        # ('BM-01.1', 'BRITADOR MÓVEL MANDÍBULA', 'CONSTRUTORA ROCHA', 'R'),
        # ('BM-01.2', 'BRITADOR MÓVEL CONE', 'CONSTRUTORA ROCHA', 'R'),
        # ('BM-01.3', 'BRITADOR MÓVEL PENEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('CA-01', 'CAMINHÃO DE ABASTECIMENTO', 'CONSTRUTORA ROCHA', 'R'),
        # ('CA-02', 'CAMINHÃO DE ABASTECIMENTO', 'CONSTRUTORA ROCHA', 'R'),
        # ('CA-02.1', 'TANQUE COMBOIO CA-02', 'CONSTRUTORA ROCHA', 'R'),
        # ('CAM-01', 'COMPRESSOR MÓVEL', 'CONSTRUTORA ROCHA', 'R'),
        # ('CAM-02', 'COMPRESSOR MÓVEL', 'CONSTRUTORA ROCHA', 'R'),
        # ('CAM-03', 'COMPRESSOR MÓVEL', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-03', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-05', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-06', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-07', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-08', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-10', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-11', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-12', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-13', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-14', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-15', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-16', 'CAMINHÃO CAÇAMBA 6X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-17', 'CAMINHÃO CAÇAMBA 6X2', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-18', 'CAMINHÃO CAÇAMBA 6X2', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-19', 'CAMINHÃO CAÇAMBA 6X2', 'CONSTRUTORA ROCHA', 'R'),
        # ('CB-20', 'CAMINHÃO CAÇAMBA 6X2', 'CONSTRUTORA ROCHA', 'R'),
        # ('CC-01', 'CAMINHÃO CARROCERIA 3X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CC-02', 'CAMINHÃO CARROCERIA 3X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CC-03', 'CAMINHÃO CARROCERIA 3X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('CE-01', 'CAMINHÃO ESPARGIDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('CE-01.1', 'IMPLEMENTO ESPARGIDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('CE-02', 'CAMINHÃO ESPARGIDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('CE-02.1', 'IMPLEMENTO ESPARGIDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('CE-03', 'CAMINHÃO ESPARGIDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('CE-03.1', 'IMPLEMENTO ESPARGIDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('CM-01', 'CAMINHÃO MUNCK', 'CONSTRUTORA ROCHA', 'R'),
        # ('CM-02', 'CAMINHÃO MUNCK', 'CONSTRUTORA ROCHA', 'R'),
        # ('CM-03', 'CAMINHÃO MUNCK', 'CONSTRUTORA ROCHA', 'R'),
        # ('COMPRESSOR-01 DESMONTEC', 'COMPRESSOR + ROQUE', 'DESMONTEC', 'T'),
        # ('COMPRESSOR-02 DESMONTEC', 'COMPRESSOR + ROQUE', 'DESMONTEC', 'T'),
        # ('COMPRESSOR-03 DESMONTEC', 'COMPRESSOR + ROQUE', 'DESMONTEC', 'T'),
        # ('COMPRESSOR-04 DESMONTEC', 'COMPRESSOR + ROQUE', 'DESMONTEC', 'T'),
        # ('COMPRESSOR-05 DESMONTEC', 'COMPRESSOR + ROQUE', 'DESMONTEC', 'T'),
        # ('CP-01', 'CAMINHÃO PIPA 10.000 LITROS', 'CONSTRUTORA ROCHA', 'R'),
        # ('CP-02', 'CAMINHÃO PIPA 15.000 LITROS', 'CONSTRUTORA ROCHA', 'R'),
        # ('CP-03', 'CAMINHÃO PIPA 15.000 LITROS', 'CONSTRUTORA ROCHA', 'R'),
        # ('CP-04', 'CAMINHÃO PIPA 15.000 LITROS', 'CONSTRUTORA ROCHA', 'R'),
        # ('CP-05', 'CAMINHÃO PIPA 10.000 LITROS', 'CONSTRUTORA ROCHA', 'R'),
        # ('CV-01 JC ROCHA', 'CAVALO MECÂNICO', 'JC ROCHA', 'T'),
        # ('CV-03', 'CAVALO MECÂNICO', 'CONSTRUTORA ROCHA', 'R'),
        # ('DJC-6E35', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('DP-03', 'DUMPER', 'CONSTRUTORA ROCHA', 'R'),
        # ('DP-04', 'DUMPER', 'CONSTRUTORA ROCHA', 'R'),
        # ('DP-05', 'DUMPER', 'CONSTRUTORA ROCHA', 'R'),
        # ('DP-06', 'DUMPER', 'CONSTRUTORA ROCHA', 'R'),
        # ('DPC-5785', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('EFN-0003', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('EH-01 JC ROCHA', 'ESCAVADEIRA HIDRAULICA', 'JC ROCHA', 'T'),
        # ('EH-01 REALMAQ', 'ESCAVADEIRA HIDÁULICA', 'REALMAQ', 'T'),
        # ('EH-02', 'ESCAVADEIRA HIDRÁULICA + ROMPEDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-02 JC ROCHA', 'ESCAVADEIRA HIDRAULICA', 'JC ROCHA', 'T'),
        # ('EH-03 JC ROCHA', 'ESCAVADEIRA HIDRAULICA', 'JC ROCHA', 'T'),
        # ('EH-04', 'ESCAVADEIRA HIDRÁULICA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-04 JC ROCHA', 'ESCAVADEIRA HIDRAULICA', 'JC ROCHA', 'T'),
        # ('EH-05', 'ESCAVADEIRA HIDRÁULICA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-06', 'ESCAVADEIRA HIDRÁULICA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-07', 'ESCAVADEIRA HIDRÁULICA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-08', 'ESCAVADEIRA HIDRÁULICA + ROMPEDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-09', 'ESCAVADEIRA HIDRÁULICA + ROMPEDOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-10', 'ESCAVADEIRA HIDRÁULICA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EH-JC ROCHA', 'ESCAVADEIRA HIDRÁULICA', 'JC ROCHA', 'T'),
        # ('EP-02', 'EMPILHADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EP-03', 'EMPILHADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('EZL-7949', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('FR-01', 'FRESADORA DE ASFALTO', 'CONSTRUTORA ROCHA', 'R'),
        # ('FR-01 TECVIA', 'FRESADORA DE ASFALTO', 'TECVIA', 'T'),
        # ('GERADOR', 'GERADOR A DIESEL', 'CAMPO SANTO', 'T'),
        # ('GG-01', 'GRUPO GERADOR', 'CONSTRUTORA ROCHA', 'R'),
        # ('GXJ-9C62', 'CAÇAMBA TERCEIRIZADA', 'IVANILDO TENÓRIO DE SOUZA', 'T'),
        # ('HCG-2554', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('HOM-5190', 'CAÇAMBA TERCEIRIZADA', 'RUBENS MEDEIROS', 'T'),
        # ('HVI-6748', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('HVM-9F56', 'L-200 (ARIMATEA ROCHA)', 'CONSTRUTORA ROCHA', 'R'),
        # ('HXA-3077', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('HZG-2554', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('IKS-8743', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('IOS-2491', 'CAVALO MECÂNICO', 'JC ROCHA', 'T'),
        # ('IRS-8743', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('JJZ-1182', 'CAÇAMBA TERCEIRIZADA', 'REGINALDO FERREIRA BARBOSA', 'T'),
        # ('JVW-1D83', 'CAÇAMBA TERCEIRIZADA', 'ANTONIO PEREIRA DA SILVA', 'T'),
        # ('KDA-2032', 'CAÇAMBA TERCEIRIZADA', 'RENATO JOSÉ DA SILVA', 'T'),
        # ('KFF-5A51', 'CAÇAMBA TERCEIRIZADA', 'JOAB DA SILVA RAMOS', 'T'),
        # ('KFN-0293', 'ÔNIBUS', 'WENDEL', 'T'),
        # ('KHS-4809', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('KIC-8873', 'F-4000', 'LINDOALDO GUEDES', 'T'),
        # ('KIN-9747', 'ÔNIBUS', 'IURY AZEVEDO', 'T'),
        # ('KIU-4317', 'CAMINHÃO PIPA', 'MARINALDO VIDAL BRITO JUNIOR', 'T'),
        # ('KJB-1D42', 'CAÇAMBA TERCEIRIZADA', 'JOSÉ ALMEIDA DA SILVA', 'T'),
        # ('KJJ-4867', 'CAÇAMBA TERCEIRIZADA ', 'IVAN VIEIRA DA ROCHA', 'T'),
        # ('KJW-4809', 'CAMINHÃO PIPA', 'RJ LOCAÇÕES', 'T'),
        # ('KJW-7152', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('KKA-4763', 'F-4000 LOCADA PARA FAZENDA', 'MAZINHO', 'T'),
        # ('KKA-7152', 'CAMINHÃO PIPA', 'RJ LOCAÇÕES', 'T'),
        # ('KKO-6A71', 'CAÇAMBA TERCEIRIZADA', 'TERTULIANO MACIEL DA SILVA NETO', 'T'),
        # ('KKY-8960', 'CHEVROLET S-10', 'ALYSSON ENCARREGADO', 'T'),
        # ('KLF-8T13', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KMC-1D26', 'CAMINHÃO PIPA TERCEIRIZADO', 'RJ LOCAÇÕES', 'T'),
        # ('KMD-0895', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('LABORATÓRIO', 'LABORATÓRIO DE ANÁLISE DE SOLO', 'CONSTRUTORA ROCHA', 'R'),
        # ('LBB-2221', 'ONIBUS', 'IURY AZEVEDO', 'T'),
        # ('LUX-0488', 'ÔNIBUS', 'IURY AZEVEDO', 'T'),
        # ('LVJ-0671', 'CAÇAMBA TERCEIRIZADA', 'JOSEFA ALVES DA SILVA GALDINO', 'T'),
        # ('LWN-1352', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('LWU-5763', 'CAMINHÃO PIPA TERCEIRZADO', 'MARINALDO VIDAL BRITO JUNIOR', 'T'),
        # ('MC-01', 'MINICARREGADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MC-01 PATOS LOCAÇÕES', 'MINICARREGADEIRA', 'PATOS LOCAÇÕES', 'T'),
        # ('MC-02', 'MINICARREGADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MMJ-5B28', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MMR-8324', 'ÔNIBUS', 'IURY AZEVEDO', 'T'),
        # ('MMV-2149', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MMW-1H80', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MN-01 JC ROCHA', 'MOTONIVELADORA', 'JC ROCHA', 'T'),
        # ('MN-02', 'MOTONIVELADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MN-02 JC ROCHA', 'MOTONIVELADORA', 'JC ROCHA', 'T'),
        # ('MN-03', 'MOTONIVELADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MN-03 JC ROCHA', 'MOTONIVELADORA', 'JC ROCHA', 'T'),
        # ('MN-04', 'MOTONIVELADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MN-05', 'MOTONIVELADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MNA-0024', 'CAÇAMBA TERCEIRIZADA', 'RONALDO FERREIRA BARBOSA', 'T'),
        # ('MNB-7269', 'CAÇAMBA TERCEIRIZADA', 'JOSÉ DE SOUSA RAMOS', 'T'),
        # ('MNK-4983', 'CAÇAMBA TERCEIRIZADA', 'JC ROCHA', 'T'),
        # ('MNK-5872', 'CAÇAMBA TERCEIRIZADA', 'FLAUMIR BARBOSA LEITE', 'T'),
        # ('MNK-7405', 'FORD F-400', 'JC ROCHA', 'T'),
        # ('MNS-2763', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MNV-3475', 'CAÇAMBA TERCEIRIZADA', 'RUBENS MEDEIROS', 'T'),
        # ('MNW-1H80', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MNY-3473', 'VEÍCULO HILLUX', 'LINDOALDO GUEDES', 'T'),
        # ('MOM-4390', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MOS-9134', 'FORD RANGER', 'CONTRUTORA ROCHA', 'R'),
        # ('MP-01', 'MANIPULADOR TELESCÓPICO', 'CONSTRUTORA ROCHA', 'R'),
        # ('MP-02', 'MANIPULADOR TELESCÓPICO', 'INTERBLOCK ', 'T'),
        # ('MP-03', 'MANIPULADOR TELESCÓPICO', 'CONSTRUTORA ROCHA', 'R'),
        # ('MVE-5302', 'CAÇAMBA TERCEIRIZADA', 'LENILSON MACIEL CATÃO DE FREITAS', 'T'),
        # ('MVE-5D02', 'CAÇAMBA TERCEIRIZADA', 'LENILSON MACIEL CATÃO DE FREITAS', 'T'),
        # ('NEZ-8920', 'F-4000', 'LINDOALDO GUEDES', 'T'),
        # ('NHA-0894', 'CAÇAMBA TERCEIRIZADA', 'LENILSON MACIEL CATÃO DE FREITAS', 'T'),
        # ('NHF-6H46', 'CAMINHÃO PIPA TERCEIRIZADO', 'JUNIOR PIPA', 'T'),
        # ('NMC-0214', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('NPU-0497', 'HILLUX (TAISON)', 'CONSTRUTORA ROCHA', 'R'),
        # ('NPW-1168', 'FRETE INTERBLOCK-PATOS', 'INTERBLOCK ', 'T'),
        # ('NPX-3201', 'VEÍCULO JC ROCHA', 'JC ROCHA', 'T'),
        # ('NQA-6180', 'VEÍCULO JC ROCHA', 'JC ROCHA', 'T'),
        # ('NQB-6540', 'CAÇAMBA TERCEIRIZADA', 'JC ROCHA', 'T'),
        # ('NQB-7764', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('NQH-6410', 'CAÇAMBA TERCEIRIZADA', 'JC ROCHA', 'T'),
        # ('NQI-5643', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('OET-1A85', 'CAÇAMBA TERCEIRIZADA', 'RUBENS MEDEIROS', 'T'),
        # ('OEU-4964', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('OEV-4964', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('OEZ-9960', 'VEÍCULO', 'INTERBLOCK ', 'T'),
        # ('OFD-1H11', 'FORD RANGER F-350', 'CONSTRUTORA ROCHA', 'R'),
        # ('OFZ-1869', 'MITSUBISH L-200 TRITON', 'CONSTRUTORA ROCHA', 'R'),
        # ('OGA-0979', 'RANGER (MARCOSXWELL)', 'CONSTRUTORA ROCHA', 'R'),
        # ('OGB-5990', 'RANGER (WALTER)', 'CONSTRUTORA ROCHA', 'R'),
        # ('OGD-6215', 'CAMINHÃO MUNCK', 'INTERBLOCK ', 'T'),
        # ('OGD-6B95', 'CAMINHÃO MUNCK', 'INTERBLOCK ', 'T'),
        # ('OLX-1171', 'CAMINHONETE', 'MARCIO FALCÃO', 'T'),
        # ('OVS-7D45', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('PC-01', 'PÁ CARREGADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('PC-01 JC ROCHA', 'PÁ CARREGADEIRA', 'JC ROCHA', 'T'),
        # ('PC-02', 'PÁ CARREGADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('PC-03', 'PÁ CARREGADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('PES-0129', 'HILLUX TOPOGRAFIA', 'CONSTRUTORA ROCHA', 'R'),
        # ('PEU-4F36', 'CAÇAMBA TERCEIRIZADA', 'JOSÉ DE ALMEIDA DA SILVA', 'T'),
        # ('PFL-5F31', 'F-350 (OFICINA)', 'CONSTRUTORA ROCHA', 'R'),
        # ('PREMOLDADO', 'PREMOLDADO', '-', 'T'),
        # ('PT-01 PROMINA', 'PLATAFORMA DE ELEVAÇÃO', 'PROMINA', 'T'),
        # ('QFG-2834', 'CAÇAMBA TERCEIRIZADA', 'JC ROCHA', 'T'),
        # ('QFJ-8346', 'CAMINHONETE AMAROK (ARLINDO)', 'CONSTRUTORA ROCHA', 'R'),
        # ('QFL-9A32', 'VEÍCULO RANGER', 'CONSTRUTORA ROCHA', 'R'),
        # ('QFN-6846', 'AMAROK', 'DANILO (ROCHA ASFALTO)', 'T'),
        # ('QFS-8346', 'AMAROK', 'CONSTRUTORA ROCHA', 'R'),
        # ('QFZ-1869', 'L-200 (MAZINHO)', 'CONSTRUTORA ROCHA', 'R'),
        # ('QFZ-9284', 'FIAT TORO', 'JC ROCHA', 'T'),
        # ('QGA-3931', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('QRF-9994', 'VEÍCULO AMAROK', 'CONSTRUTORA ROCHA', 'R'),
        # ('QSB-5990', 'VEÍCULO RANGER', 'ARIMATEA ROCHA', 'T'),
        # ('QSJ-5439', 'CAVALO MECÂNICO + CAÇAMBA', 'RAMINHO', 'T'),
        # ('QSL-8069', 'CHEVROLET S-10', 'ARIMATEA ROCHA', 'T'),
        # ('RA-01', 'RECICLADORA DE ASFALTO', 'CONSTRUTORA ROCHA (VENDIDA)', 'T'),
        # ('RANGER ARIMATEA', 'RANGER', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-01', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-01 JC ROCHA', 'ROLO COMPACTADOR VIBRATÓRIO', 'JC ROCHA', 'T'),
        # ('RCV-01 LOCAÇÕES', 'ROLO COMPACTADOR VIBRATÓRIO', 'M.G. LOCAÇÕES', 'T'),
        # ('RCV-01 REGIONAL', 'ROLO COMPACTADOR VIBRATÓRIO', 'REGIONAL', 'T'),
        # ('RCV-02', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-02 LOCAÇÕES', 'ROLO COMPACTADOR VIBRATÓRIO', 'M.G. LOCAÇÕES', 'T'),
        # ('RCV-03', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-04', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-05', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-06', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-07', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RCV-08', 'ROLO COMPACTADOR VIBRATÓRIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-01 CAMPINA LOCAÇÕES', 'RETROESCAVADEIRA', 'CAMPINA LOCAÇÕES', 'T'),
        # ('RE-01 CARVALHO', 'RETROESCAVADEIRA', 'CARVALHO', 'T'),
        # ('RE-01 JC ROCHA', 'RETROESCAVADEIRA', 'JC ROCHA', 'T'),
        # ('RE-02', 'RETROESCAVADEIRA', 'MÁQUINA VENDIDA', 'T'),
        # ('RE-02 CARVALHO', 'RETROESCAVADEIRA', 'CARVALHO', 'T'),
        # ('RE-02 JC ROCHA', 'RETROESCAVADEIRA', 'JC ROCHA', 'T'),
        # ('RE-03', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-04', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-05', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-06', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-07', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-08', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-KEKA', 'RETROESCAVADEIRA', 'KEKA', 'T'),
        # ('RESERVATÓRIO INTERBLOCK', 'RESERVATÓRIO DE DIESEL PRESENTE NA OBRA', 'INTERBLOCK ', 'T'),
        # ('RESERVATÓRIO JC ROCHA', 'TANQUE DE COMBUSTÍVEL', 'JC ROCHA', 'T'),
        # ('RLV-01', 'ROLO COMBINADO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RLV-02', 'ROLO COMBINADO', 'CONSTRUTORA ROCHA', 'R'),
        # ('RPA-01', 'ROLO DE PNEU', 'CONSTRUTORA ROCHA', 'R'),
        # ('RPA-02', 'ROLO DE PNEU', 'CONSTRUTORA ROCHA', 'R'),
        # ('RPA-03', 'ROLO DE PNEU', 'CONSTRUTORA ROCHA', 'R'),
        # ('RT-01', 'ROLO TANDEM', 'CONSTRUTORA ROCHA', 'R'),
        # ('RT-02', 'ROLO TANDEM', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-01', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-01 ALUGADO', 'TRATOR AGRÍCOLA', 'MARCELO BATATA', 'T'),
        # ('TA-01 REGIONAL', 'TRATOR AGRÍCOLA', 'REGIONAL', 'T'),
        # ('TA-02', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-03', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-04', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-05', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-06', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-07', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-08', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-09', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-10', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-11', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-12', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TA-13', 'TRATOR AGRÍCOLA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TC-02', 'TANQUE DE COMBUSTÍVEL', 'CONTRUTORA ROCHA', 'R'),
        # ('TE-01', 'TRATOR DE ESTEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TE-01 JC ROCHA', 'TRATOR DE ESTEIRAS', 'JC ROCHA', 'T'),
        # ('TE-01 REALMAQ', 'TRATOR DE ESTEIRA', 'REALMAQ', 'T'),
        # ('TE-03', 'TRATOR DE ESTEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TM.40.20P', 'TANQUE MASTER USINA', 'CONSTRUTORA ROCHA', 'R'),
        # ('VA-01', 'VIBROACABADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('VA-02', 'VIBROACABADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('VA-03', 'VIBROACABADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('VAN-01 LOCAÇÕES', 'VAN (LOCADA)', 'UNIDOS TRANSPORTE', 'T'),
        # ('NMJ-5B28', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('QQA-4763', 'CAMINHÃO BOIADEIRA', 'MAZINHO', 'T'),
        # ('JMG-3648', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('CV-JC ROCHA', 'CAVALO MECÂNICO', 'JC ROCHA', 'T'),
        # ('MNX-0424', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('LWQ-0754', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('LVS-0671', 'ONIBUS', 'YURI', 'T'),
        # ('NYH-5D07', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('QSL-9A32', 'FORD RANGER', 'ARIMATEA ROCHA', 'T'),
        # ('RE-09', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('TANQUE-JC ROCHA', 'TANQUE DE COMBUSTÍVEL', 'JC ROCHA', 'T'),
        # ('OGD-6B04', 'CAMINHÃO MUNCK', 'INTERBLOCK ', 'T'),
        # ('OYS-7D45', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('BYH-5D07', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MMU-9132', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('OGD-5B04', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('RE-10', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-01 SESUMA', 'RETROESCAVADEIRA', 'SESUMA', 'T'),
        # ('RETRO LOCADA', 'RETROESCAVADEIRA', None, 'T'),
        # ('QFA-7398', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KHA-8867', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KIL-5529', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KJK-5E39', 'FRETE PATOS', None, 'T'),
        # ('COMPRESSOR-06 DESMONTEC', 'COMPRESSOR + ROQUE', 'DESMONTEC', 'T'),
        # ('MMU-9732', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('QKO-8408', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KJG-2617', 'CAMINHÃO PIPA', 'JUNIOR PIPA', 'T'),
        # ('ROCHA PREMOLDADOS', 'ACORDO COM SÃO JUDAS TADEU', 'ROCHA PREMOLDADOS', 'T'),
        # ('JOA-5F60', 'FRETE SÃO JUDAS', None, 'T'),
        # ('MNJ-5E79', 'FRETE SÃO JUDAS', None, 'T'),
        # ('PEL-7H46', 'FRETE SÃO JUDAS', None, 'T'),
        # ('KIA-6J63', 'FRETE ROCHA PREMOLDADOS', 'ROCHA PREMOLDADOS', 'T'),
        # ('KLW-7302', 'FRETE ROCHA PREMOLDADOS', 'ROCHA PREMOLDADOS', 'T'),
        # ('OEC-6858', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('KJA-6J63', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('OGA-3931', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('OGC-6958', 'CAÇAMBA LOCADA', None, 'T'),
        # ('BVH-5D07', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('DJB-2757', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('TE-02 JC ROCHA', 'TRATOR DE ESTEIRA', 'JC ROCHA', 'T'),
        # ('IIL-1571', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KGA-9324', 'CAMINHÃO PIPA', 'JUNIOR PIPA', 'T'),
        # ('CP-06', 'CAMINHÃO PIPA 19.000 LITROS', 'CONSTRUTOA ROCHA', 'R'),
        # ('KIA-6563', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('JOA-5F50', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MMP-9A34', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('OXD7856', 'CAÇAMBA LOCADA', 'DA MATA', 'T'),
        # ('MHO-9923', 'CAÇAMBA LOCADA', 'DA MATA', 'T'),
        # ('CZC-5H30', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('HZA-9182', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('JTL-2252', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MOH-9923', 'CAÇAMBA LOCADA', 'DA MATA', 'T'),
        # ('JKH-4065', 'CAÇAMBA LOCADA', 'DA MATA', 'T'),
        # ('DJC-9E35', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MNA-6544', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MNJ-5F79', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('RE-PREMOLDADO', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MOW-7456', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('QSI-0726', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('KIQ-2225', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MAE-8J26', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('HWW-5302', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('JMG-3G48', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('QFQ-7436', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('LVK-4666', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MAE-8526', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('HZA-8192', 'FRETE INCOPOST', None, 'T'),
        # ('OGC-6458', 'CAÇAMBA LOCADA', None, 'T'),
        # ('MYW-5873', 'CAÇAMBA', 'RAMINHO', 'T'),
        # ('HUI-6748', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('KLL-3383', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MOD-8279', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MEU-2650', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('BYF-8641', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('AB-02', 'AUTOBETONEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('AB-03', 'AUTOBETONEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('MNR-1A17', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('QFO-7436', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('AJW-4C70', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('APT-OC87', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MNK-6544', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('KIA-6063', 'FRETE SÃO JUDAS', None, 'T'),
        # ('LVO-5423', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('DJE-0I21', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('GERADOR-LUZ DA LUA', 'GERADOR A DIESEL', 'LUZ DA LUA', 'T'),
        # ('MOW-0202', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('KIS-9033', 'FRETE', 'RAMINHO', 'T'),
        # ('MVE-2650', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MOM-2710', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('APT-0C87', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('IAL-2715', 'FRETE INCOPOST', None, 'T'),
        # ('MNF-9158', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MHQ-1H20', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('ASW-4670', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('HXA-3A77', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('JYM-5485', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('PES-0B29', 'HILLUX TOPOGRAFIA', 'CONSTRUTORA ROCHA', 'R'),
        # ('VL-10', 'F-350 (OFICINA)', 'CONSTRUTORA ROCHA', 'R'),
        # ('MNF-9I58', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('KEP-7C30', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MNC-8F38', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('MFE-4373', 'CAVALO MECÂNICO', 'JC ROCHA', 'T'),
        # ('MOW-6056', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('QSG-7787', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('CV-05', 'CAVALO MECÂNICO', 'CONSTRUTORA ROCHA', 'R'),
        # ('IKS-8H43', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('PC-01 DA MATA', 'PÁ CARREGADEIRA', 'MADEREIRA DA MATA', 'T'),
        # ('MYC-9478', 'CAMINHÃO COMBOIO', 'JUNIOR PIPA', 'T'),
        # ('MYC-9478 TANQUE', 'CAMINHÃO COM TANQUE PARA ABASTECIMENTO', 'JUNIOR PIPA', 'T'),
        # ('JOZ-2670', 'CAÇAMBA LOCADA', 'JUNIOR PIPA', 'T'),
        # ('PC-ALUGADA', 'PÁ CARREGADEIRA', None, 'T'),
        # ('MVB-0B45', 'CAMINHÃO BASCULANTE', None, 'T'),
        # ('MNS-2B38', 'CAVALO MECÂNICO', 'JC ROCHA', 'T'),
        # ('QSI-0796', 'FRETE ROCHA PREMOLDADOS', None, 'T'),
        # ('LAF-0229', 'CAÇAMBA LOCADA', None, 'T'),
        # ('PFH-8C23', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('HILUX JARDINS DA SERRA', 'CAMINHONETE HILLUX', 'VERIFICAR', 'T'),
        # ('OXO-7856', 'CAMINHÃO BASCULANTE', 'DA MATA', 'T'),
        # ('LAT-0829', 'ONIBUS', None, 'T'),
        # ('DYC-9E35', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('EH-05 JC ROCHA', 'ESCAVADEIRA HIDRÁULICA', 'JC ROCHA', 'T'),
        # ('RE-01 BRASIL LOCAÇÕES', 'RETROESCAVADEIRA', 'BRASIL LOCAÇÕES', 'T'),
        # ('MOB-3589', 'FRETE ASFALTO', None, 'T'),
        # ('OFH-5819', 'FRETE ASFALTO', None, 'T'),
        # ('JQR-8774', 'FRETE ASFALTO', None, 'T'),
        # ('MNH-0440', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('JQK-8774', 'FRETE ASFALTO', None, 'T'),
        # ('MZD-4A23', 'FRETE ASFALTO', None, 'T'),
        # ('QFD-8I01', 'VEÍCULO TRAIL BRAZER', 'ROBÉLIO (JARDINS)', 'T'),
        # ('EH-01 BRASIL LOCAÇÕES', 'ESCAVADEIRA HIDRÁULICA', 'BRASIL LOCAÇÕES', 'T'),
        # ('JKQ-8774', 'FRETE ASFALTO', None, 'T'),
        # ('LAF-0829', 'ONIBUS', None, 'T'),
        # ('QFX-4117', 'FORD RANGER', 'CARLOS ROCHA', 'T'),
        # ('MKO-1579', 'FRETE PATOS', None, 'T'),
        # ('RE-01 DA MATA', 'RETROESCAVADEIRA', 'DA MATA', 'T'),
        # ('PEW-6I50', 'FRETE ASFALTO', None, 'T'),
        # ('NVG-5G86', 'FRETE INTERBLOCK-PATOS', None, 'T'),
        # ('MPH-9308', 'FRETE ASFALTO', None, 'T'),
        # ('HGT-1A85', 'FRETE ASFALTO', None, 'T'),
        # ('KXJ-9C62', 'FRETE ASFALTO', None, 'T'),
        # ('PEW-6150', 'FRETE ASFALTO', None, 'T'),
        # ('MZB-4A23', 'FRETE ASFALTO', None, 'T'),
        # ('MNF-1943', 'FRETE ASFALTO', None, 'T'),
        # ('OGT-1A85', 'FRETE ASFALTO', None, 'T'),
        # ('LJG-6149', 'ONIBUS', None, 'T'),
        # ('KFJ-3B49', 'ONIBUS', None, 'T'),
        # ('FQA-0J50', 'CAMINHONETE S-10', None, 'T'),
        # ('EH-02 JC-ROCHA', 'ESCAVADEIRA HIDRÁULICA', 'JC ROCHA', 'T'),
        # ('EH-01 NORMAQ', 'ESCAVADEIRA HIDRÁULICA', 'NORMAQ', 'T'),
        # ('MNU-5A58', 'FRETE ASFALTO', None, 'T'),
        # ('MNB-1B93', 'FRETE ASFALTO', None, 'T'),
        # ('PGP-0632', 'CAÇAMBA LOCADA', None, 'T'),
        # ('GVQ-1E03', 'CAÇAMBA LOCADA', None, 'T'),
        # ('MPH-9304', 'FRETE ASFALTO', None, 'T'),
        # ('JVW-1B83', 'FRETE ASFALTO', None, 'T'),
        # ('KSJ-5439', 'CAVALO MECÂNICO', 'RAMINHO', 'T'),
        # ('MOC-8D52', 'FRETE ASFALTO', None, 'T'),
        # ('EGJ-8A97', 'VAN (LOCADA)', None, 'T'),
        # ('NPV-5230', 'CAÇAMBA LOCADA', None, 'T'),
        # ('MPV-5230', 'FRETE ASFALTO', None, 'T'),
        # ('KFJ-3B48', 'FRETE ASFALTO', None, 'T'),
        # ('KIJ-2012', 'FRETE ASFALTO', None, 'T'),
        # ('RLS-8J33', 'FRETE ASFALTO', None, 'T'),
        # ('TA-02 JC ROCHA', 'TRATOR AGRÍCOLA', 'JC ROCHA', 'T'),
        # ('GG-01 LOCADO', 'GERADOR A DIESEL', 'A GERADORA', 'T'),
        # ('GG-02 LOCADO', 'GERADOR A DIESEL', 'A GERADORA', 'T'),
        # ('ANV-7B72', 'FRETE ASFALTO', None, 'T'),
        # ('QSJ-5934', 'CAVALO MECÂNICO', 'RAMINHO', 'T'),
        # ('MNM-5460', 'FRETE ASFALTO', None, 'T'),
        # ('RE-01 INCORPORA', 'RETROESCAVADEIRA', 'INCORPORADORA', 'T'),
        # ('KJX-0A11', 'FRETE ASFALTO', None, 'T'),
        # ('RLU-7G25', 'FRETE ASFALTO', None, 'T'),
        # ('KDL-L531', 'FRETE ASFALTO', None, 'T'),
        # ('MNM-5046', 'FRETE ASFALTO', None, 'T'),
        # ('MNF-6H58', 'FRETE ASFALTO', None, 'T'),
        # ('IMB-900', 'MÁQUINA MEIO FIO', 'CONSTRUTORA ROCHA', 'R'),
        # ('OFA-8229', 'CAÇAMBA LOCADA', None, 'T'),
        # ('NPZ-7772', 'FRETE ASFALTO', None, 'T'),
        # ('JRJ-3H18', 'FRETE ASFALTO', None, 'T'),
        # ('KDL-1531', 'FRETE ASFALTO', None, 'T'),
        # ('NPZ-7722', 'FRETE ASFALTO', None, 'T'),
        # ('NQZ-7772', 'FRETE ASFALTO', None, 'T'),
        # ('CLU-7419', 'VAN LOCADA', None, 'T'),
        # ('RE-01 ARENA ENGENHARIA', 'RETROESCAVADEIRA', 'ARENA ENGENHARIA', 'T'),
        # ('KFM-0293', 'ONIBUS', None, 'T'),
        # ('CKG-0455', 'FRETE ASFALTO', None, 'T'),
        # ('EH-01 RMS', 'ESCAVADEIRA HIDRÁULICA', None, 'T'),
        # ('GXM-3622', 'FRETE ASFALTO', None, 'T'),
        # ('GSB-5144', 'FRETE ASFALTO', None, 'T'),
        # ('DIFERENÇA', 'VERIFICAÇÃO', None, 'T'),
        # ('CA-01 AGUIA', 'CAMINHÃO COMBOIO', 'ÁGUIA TURISMO', 'T'),
        # ('VAN-02 LOCAÇÕES', 'VAN LOCADA LQT-2557', None, 'T'),
        # ('HOF-6F11', 'FRETE ASFALTO', None, 'T'),
        # ('QFE-5515', 'FRETE ASFALTO', None, 'T'),
        # ('EH-01 SOLIDO', 'ESCAVADEIRA HIDRÁULICA', 'SOLIDO', 'T'),
        # ('EH-01 HGR', 'ESCAVADEIRA HIDRÁULICA', 'HGR', 'T'),
        # ('NQH-6J39', 'FRETE ASFALTO', None, 'T'),
        # ('MNK-3698', 'FRETE ASFALTO', None, 'T'),
        # ('HOO-6F11', 'CAÇAMBA FRETE', None, 'T'),
        # ('NNJ-2D47', 'CAÇAMBA LOCADA', None, 'T'),
        # ('JOY-6781', 'FRETE ASFALTO', None, 'T'),
        # ('HPW-1114', 'FRETE ASFALTO', None, 'T'),
        # ('NQH-LJ39', 'FRETE ASFALTO', None, 'T'),
        # ('NPZ-5903', 'FRETE ASFALTO', None, 'T'),
        # ('LQT-2557', 'VAN ASFALTO', None, 'T'),
        # ('MNM-7358', 'FRETE ASFALTO', None, 'T'),
        # ('NAF-0829', 'FRETE ASFALTO', None, 'T'),
        # ('CVQ-1E03', 'CAÇAMBA LOCADA', None, 'T'),
        # ('NNT-9G04', 'FRETE ASFALTO', None, 'T'),
        # ('MOTOR BOMBA', 'MOTOR BOMBA FAZENDA', 'FAZENDA ARIMATE', 'T'),
        # ('PC-01 INTERBLOCK', 'PÁ CARREGADEIRA', 'INTERBLOCK ', 'T'),
        # ('MNJ-2D47', 'CAVALO MECÂNICO', 'RAMINHO', 'T'),
        # ('LIMPEZA', 'DIESEL PARA LIMPEZA DE EQUIPAMENTOS', None, 'T'),
        # ('MN-06', 'MOTONIVELADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('OEZ-8637', 'CAÇAMBA LOCADA', None, 'T'),
        # ('NNG-9G04', 'RANGER', 'MAZINHO', 'T'),
        # ('AUQ-9787', 'FRETE', None, 'T'),
        # ('OFF-4139', 'FRETE', None, 'T'),
        # ('MN-07', 'MOTONIVELADORA', 'CONSTRUTORA ROCHA', 'R'),
        # ('RE-11', 'RETROESCAVADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('KJE-3606', 'CAMINHÃO LOCADO', None, 'T'),
        # ('JKW-1881', 'ONIBUS', None, 'T'),
        # ('PEX-1D42', 'CAÇAMBA LOCADA', None, 'T'),
        # ('GUK-3H68', 'CAÇAMBA LOCADA', None, 'T'),
        # ('ETC-0B25', 'CAÇAMBA LOCADA', None, 'T'),
        # ('GVK-3H68', 'CAÇAMBA LOCADA', None, 'T'),
        # ('PEV-8J41', 'CAÇAMBA LOCADA', None, 'T'),
        # ('LUW-7481', 'CAÇAMBA LOCADA', None, 'T'),
        # ('FUB-2A40', 'AMAROK', 'SANDRO CALÇAMENTO', 'T'),
        # ('QFB-7B31', None, None, 'T'),
        # ('SKX-7J03', 'CHEVROLET S-10', 'ARIMATEA ROCHA', 'T'),
        # ('HTV-4J01', 'F-4000', 'JUAZEIRINHO', 'T'),
        # ('EH-11', 'ESCAVADEIRA HIDRÁULICA', 'ROCHA ASFALTO', 'T'),
        # ('EH-02 PAULO LOCAÇÕES', 'ESCAVADEIRA HIDRÁULICA', 'PAULO', 'T'),
        # ('KIG-9463', 'CAMINHÃO CAÇAMBA', None, 'T'),
        # ('FGD-8C52', 'CAMINHÃO CAÇAMBA', None, 'T'),
        # ('KKA-6471', 'CAMINHÃO CAÇAMBA', None, 'T'),
        # ('MC-03', 'MINICARREGADEIRA', 'CONSTRUTORA ROCHA', 'R'),
        # ('PCK-3B40', 'FRETE ASFALTO', None, 'T'),
        # ('CB-22', 'CAMINHÃO CAÇAMBA', 'CONSTRUTORA ROCHA', 'R'),
        # ('PFF-8528', 'CAÇAMBA LOCADA', None, 'T'),
        # ('MTS-2338', 'CAÇAMBA LOCADA', None, 'T'),
        # ('MNJ-5A58', 'CAÇAMBA LOCADA', None, 'T'),
        # ('BMQ-3651', 'CAÇAMBA LOCADA', None, 'T'),
        # ('CB-21', 'CAMINHÃO CAÇAMBA', 'CONSTRUTORA ROCHA', 'R'),
        # ('HDV-4J01', 'CAÇAMBA LOCADA', None, 'T'),
        # ('QFK-1B01', 'CAVALO MECÂNICO', 'RAMINHO', 'T'),
        # ('MOW-6887', 'L-200', None, 'T'),
        # ('QFV-3A13', 'HILLUX', 'MARCOSXWELL ENCARREGADO', 'T'),
        # ('OEV-3259', 'CAÇAMBA LOCADA', None, 'T'),
        # ('OFD-1948', 'CAÇAMBA LOCADA', None, 'T'),
        # ('PC-INTERBLOCK', 'PÁ CARREGADEIRA', 'INTERBLOCK ', 'T'),
        # ('MN-ALAGOA NOVA', 'MOTONIVELADORA', 'PREFEITURA ALAGOA NOVA', 'T'),
        # ('NQE-2747', 'CAMINHÃO CARROCERIA 3X4', None, 'T'),
        # ('NPZ-9B94', 'CAÇAMBA LOCADA', None, 'T'),
        # ('LVW-0978', 'CAÇAMBA LOCADA', None, 'T'),
        # ('MMZ-0G58', 'PIPA LOCADO', None, 'T'),
        # ('NQE-5747', 'CAMINHÃO CARROCERIA 3X4', None, 'T'),
        # ('CA-01 REGIONAL', 'CAMINHÃO COMBOIO', 'REGIONAL', 'T'),
        # ('CC-04', 'CAMINHÃO CARROCERIA 3X4', 'CONSTRUTORA ROCHA', 'R'),
        # ('RLX-1H56', 'HILLUX', 'ARIMATEA ROCHA', 'T'),
        # ('MNJ-5B28', 'CAÇAMBA LOCADA', None, 'T'),
        # ('PEL-9450', 'CAMINHÃO PIPA LOCADO', None, 'T'),
        # ('QIZ-4F62', 'SERVIÇO SINALIZAÇÃO', None, 'T'),
        # ('KHI-3974', 'CAÇAMBA LOCADA', None, 'T'),
        # ('KKH-9682', 'CAÇAMBA LOCADA', None, 'T'),
        # ('QFX-4B17', 'RANGER', 'CONSTRUTORA ROCHA', 'R'),
        # ('ESCAVADEIRA LOCADA', 'ESCAVADEIRA HIDRÁULICA', 'LOCADA', 'T'),
        # ('FDJ-8C52', 'CAMINHÃO SINALIZAÇÃO', None, 'T'),
        # ('QSM-8H78', 'S-10', None, 'T'),
        # ('QYJ-2E21', 'CAMINHÃO', 'TECVIA', 'T'),
        # ('MMP-1793', 'CAMINHÃO PIPA', None, 'T'),
        # ('KLH-9C20', 'CAMINHÃO SINALIZAÇÃO', None, 'T'),
        # ('MMS-0G58', 'CAMINHÃO PIPA LOCADO', None, 'T'),
        # ('RESERVATÓRIO FAZENDA', 'TAMBOR DE DIESEL FAZENDA', None, 'T'),
        # ('KIE-3606', 'CAÇAMBA LOCADA', None, 'T'),
        # ('NQF-4024', 'CAÇAMBA LOCADA', None, 'T'),
        # ('LWC-1G64', 'CAMINHÃO PIPA LOCADO', None, 'T'),
        # ('RLV-7625', 'CAMINHÃO TERCEIRIZADO', None, 'T'),
        # ('QMF-4H28', 'TOYOTA HILLUX', 'EUDES TOPÓGRAFO', 'T'),
        # ('RE-01 PROMINA', 'RETROESCAVADEIRA', 'PROMINA', 'T'),
        # ('MNH-1E48', 'CAÇAMBA LOCADA', None, 'T'),
        # ('EH-01 BMC', 'ESCAVADEIRA HIDRÁULICA', 'BMC', 'T'),
        # ('KGS-7339', 'PIPA LOCADO', None, 'T'),
        # ('GUR-0F42', 'CAMINHÃO 3/4', None, 'T'),
        # ('QFX-1B01', 'CAÇAMBA TERCEIRIZADA', 'RAMINHO', 'T'),
        # ('RE-01 FTMAQ', 'RETROESCAVADEIRA', 'FTMAQ', 'T'),
        # ('EH-01 CARVALHO', 'ESCAVADEIRA HIDRÁULICA', 'CARVALHO', 'T'),
        # ('KXL-3E40', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('RE-01 METRAX', 'RETROESCAVADEIRA', 'METRAX', 'T'),
        # ('JOZ-8H83', 'PIPA LOCADO', None, 'T'),
        # ('TE-01 CARVALHO', 'TRATOR DE ESTEIRA', 'CARVALHO', 'T'),
        # ('RE-01 WL', 'RETROESCAVADEIRA', 'WL', 'T'),
        # ('MIF-0C36', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('XXJ-3E40', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('KOE-9C60', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('MC-04', 'MINICARREGADEIRA', 'CONTRUTORA ROCHA', 'R'),
        # ('RE-01 REALMAQ', 'RETROESCAVADEIRA', 'REALMAQ', 'T'),
        # ('JAJ-9B58', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('SKY-3C16', 'CAÇAMBA FRETE', None, 'T'),
        # ('QSE-5D89', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('OEX-4F87', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('KXJ-3E40', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('RE-01 HYPE', 'RETROESCAVADEIRA', 'HYPE', 'T'),
        # ('EH-01 MG', 'ESCAVADEIRA HIDRÁULICA', 'MG', 'T'),
        # ('QRE-5B89', 'CAÇAMBA TERCEIRIZADO', None, 'T'),
        # ('MN-01 CONSERV', 'MOTONIVELADORA', 'CONSERV', 'T'),
        # ('PSZ-2A72', 'FRETE TERCEIRIZADO', None, 'T'),
        # ('MNA-0A24', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('JUX-4G13', 'CAÇAMBA TERCEIRIZADA', None, 'T'),
        # ('KIG-9E63', 'CAÇAMBA TERCEIRIZADA', None, 'T'),]

        for i in lista_equipamentos:
            print(i[0], i[1], i[2], i[3])

            # cadastro_equipamentoss = Equipamentos(prefixo=i[0],
            #                                         descricao=i[0],
            #                                         tipo=i[3],
            #                                         proprietario=i[2],
            #                                         horímetro=0)

        # cadastro_equipamentoss.save()

        





        
        # Método para atualizar saldo da obra.
        for obra in obras:
            
            saldo = Entrada.objects.filter(obra=obra)  and Abastecimento.objects.filter(obra=obra)
            # if saldo == None:                
            #     obra.saldo = 0
            # else:
            #     obra.saldo = Entrada.objects.filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum'] - Abastecimento.objects.filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
            # obra.save()

        #Método para atualizar saldo dos tanques e lançar valores no frontend
        for tanque in tanques:
            if tanque.tipo == "F":
                tanque.estoque = nonetest(Entrada.objects.filter(tanque=tanque).aggregate(Sum('quantidade'))['quantidade__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum']) - nonetest(Transferencia.objects.filter(fixo=tanque).aggregate(Sum('litros'))['litros__sum'])
            if tanque.tipo == 'M':
                tanque.estoque = nonetest(Transferencia.objects.filter(movel=tanque).aggregate(Sum('litros'))['litros__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum'])
            
            tanque.save()
            if tanque.prefixo == 'TC-01':
                tc01 = [tanque.estoque, round(100*tanque.estoque/15000),1]
                
            elif tanque.prefixo == 'TC-02':
                tc02 = [tanque.estoque, round(100*tanque.estoque/30000, 1)]
            elif tanque.prefixo == 'CA-01.1':
                ca01 = [tanque.estoque, round(100*tanque.estoque/4200,1)]
            elif tanque.prefixo == 'CA-02.1':
                ca02 = [tanque.estoque, round(100*tanque.estoque/4500,2)]
        estoque_total = tc01[0]+tc02[0]+ca01[0]+ca02[0]
        porcent_estoque = round(100*(estoque_total/(15000+30000+4200+4500)),1)
        #Alterações horímetro equipamento
        for equipamento in equipamentos:

            equipamento.save()

        #criação de gráfico semanal no frontend
        ano = datetime.today().year
        mes = datetime.today().month
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

        mes_atual = request.POST.get('mes')
        if mes_atual == None:
            mes_atual = meses[mes-1]
        mes = meses.index(mes_atual)+1
        print(mes_atual, mes)        

        data_inicio_1 = datetime(ano,mes,1)
        data_fim_1 = datetime(ano, mes, 8)
        data_inicio_2 = datetime(ano,mes,9)
        data_fim_2 = datetime(ano, mes, 16)
        data_inicio_3 = datetime(ano,mes,17)
        data_fim_3 = datetime(ano, mes, 24)
        data_inicio_4 = datetime(ano,mes,25)
        if mes == 'Janeiro' or mes =='Março' or mes =='Maio' or mes =='Julho' or mes =='Agosto' or mes =='Outubro' or mes =='Dezembro':
            data_fim_4 = datetime(ano, mes, 31)
        if mes == 'Abril' or mes =='Junho' or mes =='Setembro' or mes =='Novembro':
            data_fim_4 = datetime(ano, mes, 30)
        else:
            data_fim_4 = datetime(ano, mes, 28)



        entradas_1 = Entrada.objects.filter(data_entrega__range=[data_inicio_1, data_fim_1]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas_2 = Entrada.objects.filter(data_entrega__range=[data_inicio_2, data_fim_2]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas_3 = Entrada.objects.filter(data_entrega__range=[data_inicio_3, data_fim_3]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas_4 = Entrada.objects.filter(data_entrega__range=[data_inicio_4, data_fim_4]).aggregate(Sum('quantidade'))['quantidade__sum']
        entradas = json.dumps([entradas_1, entradas_2, entradas_3, entradas_4])

        saidas_1 = Abastecimento.objects.filter(data__range=[data_inicio_1, data_fim_1]).aggregate(Sum('litros'))['litros__sum']
        saidas_2 = Abastecimento.objects.filter(data__range=[data_inicio_2, data_fim_2]).aggregate(Sum('litros'))['litros__sum']
        saidas_3 = Abastecimento.objects.filter(data__range=[data_inicio_3, data_fim_3]).aggregate(Sum('litros'))['litros__sum']
        saidas_4 = Abastecimento.objects.filter(data__range=[data_inicio_4, data_fim_4]).aggregate(Sum('litros'))['litros__sum']
        saidas = json.dumps([saidas_1, saidas_2, saidas_3, saidas_4])   

        lista_obras = []
        lista_consumo = []

        
        #criação de gráfico obras no frontend
        for obra in obras:
            consumo_mensal_obras = Abastecimento.objects.filter(data__month=mes).filter(data__year=ano).filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
            lista_obras.append(obra.nome)
            if consumo_mensal_obras == None:
                consumo_mensal_obras = 0
            lista_consumo.append(consumo_mensal_obras)
        
        list_obras=(lista_obras)
        list_consumo = json.dumps(lista_consumo)

        equipamentos = Equipamentos.objects.all()
        list_equip = []
        saidas_equip = []
        for equipamento in equipamentos:
            list_equip.append(equipamento.prefixo)
            saida_equip = Abastecimento.objects.filter(data__month=mes).filter(data__year=ano).filter(equipamento=equipamento).aggregate(Sum('litros'))['litros__sum']
            if saida_equip == None:
                saida_equip = 0
            saidas_equip.append(saida_equip)

            
        #LISTA EQUIPAMENTOS MAIOR CONSUMO
        dict_equip = dict(zip(list_equip,saidas_equip))
        sort_dict = dict(sorted(dict_equip.items(), key=itemgetter(1), reverse=True))
        sort_d = dict(list(sort_dict.items())[:5])


        return render(request, 'home.html', {'tanques':tanques, 
                                             'obras': obras, 
                                             'meses':meses,
                                             'equipamentos':equipamentos, 
                                             'user':user, 
                                            #  'obra_user':obra_user[0], 
                                             'tc01':tc01,
                                             'tc02':tc02,
                                             'ca01':ca01,
                                             'ca02':ca02,
                                             'estoque_total':estoque_total,
                                             'porcent_estoque':porcent_estoque,
                                             'mes_atual':mes_atual,
                                             'entradas':entradas,
                                             'saidas':saidas,
                                             'list_obras':list_obras,
                                             'list_consumo':list_consumo,
                                             'sort_dict':sort_d,})
    
    if request.method == 'POST':
        form_saidas = request.POST.get('form_saidas')
        form_transferencias = request.POST.get('form_transferencias')
        form_entradas = request.POST.get('form_entradas')
        form_test = request.POST.get('form_test')

# método acima é para quando for necessário selecionar um form específico em um html com mais de um form

        if form_saidas:

            tanque_id = request.POST.get('tanque_id')
            tanque = Tanque.objects.get(id=tanque_id)
            obra_id = request.POST.get('obra') #Método para buscar o id de uma ForeignKey
            obra = Obras.objects.get(id=obra_id)
            equipamento_id = request.POST.get('equipamento')
            equipamento =Equipamentos.objects.get(id=equipamento_id)
            
            contador_inicial = request.POST.get('contador_inicial')
            contador_final = request.POST.get('contador_final')
            litros = request.POST.get('saida_litros')
            horimetro = request.POST.get('horimetro')
            operador = request.POST.get('operador')
            data = date.today()
            num_saida = Abastecimento.objects.aggregate(Max('numero'))
            num_saida = (num_saida['numero__max'] + 1)



            #lançamento abastecimentos:
            abastecimento = Abastecimento(litros=litros,
                                          contador_inicio=contador_inicial,
                                          contador_fim=contador_final,
                                          horimetro=horimetro,
                                          data=data,
                                          tanque=tanque,
                                          obra=obra,
                                          equipamento=equipamento,
                                          operador=operador,
                                          colaborador= request.user,
                                          numero=num_saida)
            try:
                abastecimento.save()

                messages.add_message(request, constants.SUCCESS, "Abastecimento laçado com sucesso!" )
                return redirect("/ceq/home")
            except:
                messages.add_message(request, constants.ERROR, "ERRO AO LANÇAR O ABASTECIMENTO" )
                return redirect("/ceq/home")




            print(f"{tanque}, {obra}, {equipamento}, {contador_inicial}, {contador_final}, {type(litros)},{horimetro}, {operador}")
            return HttpResponse(f"{data}, {equipamento}, {contador_inicial}, {contador_final}, {litros},{horimetro}, {operador} -- ,tanque:{tanque}  tanque.saldo: {tanque.estoque} -- obra:{obra}, saldo:{obra.saldo}")
        
        
        if form_entradas:

            tanque_id = request.POST.get('tanque_id')
            tanque = Tanque.objects.get(id=tanque_id)
            obra_id = request.POST.get('obra_id')
            obra = Obras.objects.get(id=obra_id)
            data_emissao = request.POST.get('data_nf')
            data_entrega = request.POST.get('data_entrega')
            fornecedor = request.POST.get('fornecedor')
            nota_fiscal = request.POST.get('NF')
            valor_litro = request.POST.get('valor_litro')
            quantidade_litros = request.POST.get('quantidade')
            valor_total = float(valor_litro) * int(quantidade_litros)
            num_entrada = Entrada.objects.aggregate(Max('numero'))
            num_entrada = num_entrada['numero__max']+1

            #lançamento entradas:
            entrada = Entrada(tanque=tanque,
                              nota_fiscal=nota_fiscal,
                              fornecedor=fornecedor,
                              data_nf=data_emissao,
                              data_entrega=data_entrega,
                              obra=obra,
                              quantidade=quantidade_litros,
                              preco_unitario=valor_litro,
                              preco_total=valor_total,
                              colaborador=request.user,
                              numero=num_entrada
                              )
            entrada.save()

            #Método para atualizar saldo dos tanques.
            total_entradas = nonetest(Entrada.objects.filter(tanque=tanque).aggregate(Sum('quantidade'))['quantidade__sum'])
            total_saidas = nonetest(Abastecimento.objects.filter(tanque=tanque).aggregate(Sum('litros'))['litros__sum'])
            total_transferências = nonetest(Transferencia.objects.filter(fixo=tanque).aggregate(Sum('litros'))['litros__sum'])
            tanque.estoque = total_entradas - total_saidas - total_transferências
            tanque.save()
            
            #Método para atualizar saldo da obra.
            total_entradas = nonetest(Entrada.objects.filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum'])
            total_saidas = nonetest(Abastecimento.objects.filter(obra=obra).aggregate(Sum('litros'))['litros__sum'])
            obra.saldo = total_entradas - total_saidas
            obra.save()
            print(f"obra:{obra} ---saldo_obra = {obra.saldo} --- estoque_tanque = {tanque.estoque}")
            return HttpResponse(f"{tanque}, {obra_id}, {type(data_emissao)}, {type(data_entrega)}, {fornecedor}, {nota_fiscal},{valor_litro}, {quantidade_litros}")

        
        if form_transferencias:
            tanque_fixo_id = request.POST.get('tanque_fixo_id')
            tanque_fixo = Tanque.objects.get(id=tanque_fixo_id)
            tanque_movel_id = request.POST.get('tanque_movel_id')
            tanque_movel = Tanque.objects.get(id=tanque_movel_id)

            contador_inicial = request.POST.get('contador_inicio')
            contador_final = request.POST.get('contador_fim')
            litros = float(contador_final) - float(contador_inicial)
            contador_comboio = request.POST.get('contador_comboio')
            data = date.today()

            #lançamento transferências:
            transferencia = Transferencia(fixo=tanque_fixo,
                                          movel=tanque_movel,
                                          contador_inicio=float(contador_inicial),
                                          contador_fim=float(contador_final),
                                          litros=litros,
                                          contador_comboio=float(contador_comboio),
                                          colaborador=request.user,
                                          data=date.today())
            
            transferencia.save()
            #Método para atualizar saldo dos tanques.
            tanque_fixo.estoque = nonetest(Entrada.objects.filter(tanque=tanque_fixo).aggregate(Sum('quantidade'))['quantidade__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque_fixo).aggregate(Sum('litros'))['litros__sum']) - nonetest(Transferencia.objects.filter(fixo=tanque_fixo).aggregate(Sum('litros'))['litros__sum'])
            tanque_movel.estoque = nonetest(Transferencia.objects.filter(movel=tanque_movel).aggregate(Sum('litros'))['litros__sum']) - nonetest(Abastecimento.objects.filter(tanque=tanque_movel).aggregate(Sum('litros'))['litros__sum'])
                
            
            tanque_fixo.contador = float(contador_final)
            tanque_movel.contador = float(contador_comboio)
            tanque_fixo.save()
            tanque_movel.save()

            print(f"{tanque_fixo.estoque}, {tanque_movel.estoque}")

            return HttpResponse(f"{tanque_fixo}, {tanque_movel}, {type(contador_inicial)}, {contador_final}, {contador_comboio}, LITROS:{litros}")

    else: return HttpResponse('<h1>Acesso negado</h1>')

@login_required(login_url='/auth/login/')
def saidas(request):
 if request.user.status=='c':
        
    obras = Obras.objects.all()
    equipamentos = Equipamentos.objects.all()
    list_equipamentos = []
    list_obras =[]

    for e in equipamentos:list_equipamentos.append(e)
    for o in obras: list_obras.append(o)
    

    data_inicio = request.POST.get('data_inicio')
    if data_inicio == None or data_inicio == '': datetime.strptime('2020-01-02', '%Y-%m-%d').date()
    else: data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
    data_fim = request.POST.get('data_fim')
    if data_fim == None or data_fim == '': data_fim = date.today()
    else: data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()


    filtro_obras = request.POST.getlist('obra')
    filtro_equipamento = request.POST.getlist('equipamento')
    
    if data_inicio or data_fim or filtro_equipamento or filtro_obras:
        if not data_inicio:
            data_inicio = date(2020,1,1)
        if not data_fim:
            data_fim = date.today()
        if not filtro_equipamento:
            filtro_equipamento = list_equipamentos
        if not filtro_obras:
            filtro_obras= list_obras


        saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).filter(equipamento__in=filtro_equipamento).filter(obra__in=filtro_obras).order_by('numero')
        total_saidas = Abastecimento.objects.filter(data__range=[data_inicio, data_fim]).filter(equipamento__in=filtro_equipamento).filter(obra__in=filtro_obras).aggregate(Sum('litros'))['litros__sum']

    else:
        saidas = Abastecimento.objects.all().order_by('numero')
    user = request.user
    obra_user=Obras.objects.filter(usuario=user.id)
    print(type(data_fim), data_fim)
    print(type(data_inicio), data_inicio)
    print(total_saidas)
    
    return render(request, 'saidas.html', {'saidas': saidas, 
                                           'obras': obras, 
                                           'equipamentos':equipamentos, 
                                           "user":user, 
                                           'total_saidas':total_saidas})
 
 elif request.user.status == 'o': 
    return HttpResponse('acesso negado')

@login_required(login_url='/auth/login/')
def entradas(request):
  if request.user.status=='c':

    obras = Obras.objects.all()

    list_obras = []
    for i in obras: list_obras.append(i)

    #filtro
    filtro_obra = request.POST.getlist('obra')
    data_inicio = request.POST.get('data_inicio')
    data_fim = request.POST.get('data_fim')

    if data_inicio or data_fim or filtro_obra:
        if not data_inicio:
            data_inicio = date(2020,1,1)
        elif data_inicio == None:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if not data_fim:
            data_fim = date.today()
        elif data_fim == None:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        if not filtro_obra:
            filtro_obra = list_obras

    if request.method == "GET":
        if not data_inicio:
            data_inicio = date(2020,1,1)
        elif data_inicio == None:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if not data_fim:
            data_fim = date.today()
        elif data_fim == None:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        if not filtro_obra:
            filtro_obra = list_obras

        
        entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).order_by('numero')
        total_entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).aggregate(Sum('quantidade'))['quantidade__sum']
    else:
        entradas = Entrada.objects.all().order_by('numero')
        total_entradas = Entrada.objects.filter(data_entrega__range=[data_inicio, data_fim], obra__in=filtro_obra).aggregate(Sum('quantidade'))['quantidade__sum']


    print(f"{filtro_obra} and {type(filtro_obra)}")
    print(f"{data_inicio} and {type(data_inicio)}")
    user = request.user
    obra_user=Obras.objects.filter(usuario=user.id)
    print(entradas)

    return render(request, 'entradas.html', {'entradas':entradas, 
                                             'obras': obras, 
                                             "user":user, 
                                             'total_entradas':total_entradas})
  else: return HttpResponse("<h1>Acesso negado</h1>")

def transferencias(request):
 if request.user.status == "c":

    transferencias = Transferencia.objects.all()
    tanque_fixo = Tanque.objects.filter(tipo='F')
    tanque_movel = Tanque.objects.filter(tipo='M')

    print(tanque_movel)
    data_inicio = request.POST.get('data_inicio')
    data_fim = request.POST.get('data_fim')
    tanque = request.POST.getlist('tanque_fixo')
    comboio = request.POST.getlist('tanque_movel')
    
    if data_inicio or data_fim or tanque or comboio:
        if not data_inicio:
            data_inicio = date(2022,1,1)
        else:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if not data_fim:
            data_fim = date.today()
        else:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        if not tanque:
            tanque = tanque_fixo
        if not comboio:
            comboio = tanque_movel
        
        transferencias = Transferencia.objects.filter(movel__in=comboio, fixo__in=tanque, data__range=[data_inicio, data_fim])
            


    return render(request, 'transferencias.html', {'transferencias': transferencias, 'tanque_fixo':tanque_fixo, 'tanque_movel':tanque_movel})
 else: return HttpResponse('<h1>Acesso Negado</h1>')


def obras(request):

 if request.user.status == "c":
    obras = Obras.objects.all()
    saidas = []
    entradas = []
    
    for obra in obras:
        metodo_saidas = Abastecimento.objects.filter(obra=obra).aggregate(Sum('litros'))['litros__sum']
        metodo_entradas = Entrada.objects.filter(obra=obra).aggregate(Sum('quantidade'))['quantidade__sum']
        if metodo_saidas == None:
            metodo_saidas = 0
        if metodo_entradas == None:
            metodo_entradas = 0

        obra.saldo = metodo_entradas - metodo_saidas
        obra.save()
        saidas.append(metodo_saidas)
        entradas.append(metodo_entradas)

    my_list = zip(obras, saidas, entradas)
    return render(request, 'obras.html', {'my_list': my_list})
 else: return HttpResponse("<h1>Acesso Negado</h1>")

def painel_obras(request):
 if request.user.status == "c":

    saidas = Abastecimento.objects.filter(status=False)

    return render(request, "painel_obras.html", {"saidas":saidas})
 else: return HttpResponse("<h1>Acesso Negado</h1>")


def obras_ano(request):
 if request.user.status == 'c':
    if request.method == "GET":
        year = datetime.today().year
    elif request.method == "POST":
        year = request.POST.get("ano")

    g_vunit = grafico_vunit(year)    

    yearb = int(year)-1
    lista =[]
    obras = Obras.objects.all()
    for obra in obras:
        l=[]
        l.append(obra.nome)
        for n in range(1,13):
            total_saidas = nonetest(Abastecimento.objects.filter(obra=obra).filter(data__year=year).filter(data__month=n).aggregate(Sum('litros'))['litros__sum'])
            total_obra = nonetest(Abastecimento.objects.filter(obra=obra).filter(data__year=year).aggregate(Sum('litros'))['litros__sum'])
            l.append(total_saidas)
        l.append(total_obra)
        lista.append(l)  


    saidas_meses = []
    entradas_meses = []
    entradas_meses_valor = []
    preco_unitario_meses =[]
    valor_saidas_meses =[]
    saldo_meses =[]
    saldo_acumulado_meses =[]
    for m in range(1,13):    
        saidas_mes = nonetest(Abastecimento.objects.filter(data__month=m).filter(data__year=year).aggregate(Sum('litros'))['litros__sum'])
        entradas_mes = nonetest(Entrada.objects.filter(data_entrega__month=m).filter(data_entrega__year=year).aggregate(Sum('quantidade'))['quantidade__sum'])
        entradas_mes_valor = nonetest(Entrada.objects.filter(data_entrega__month=m).filter(data_entrega__year=year).aggregate(Sum('preco_total'))['preco_total__sum'])
        preco_unitario_mes = nonetest(Entrada.objects.filter(data_entrega__month=m).filter(data_entrega__year=year).aggregate(Avg('preco_unitario'))['preco_unitario__avg'])
        
        saidas_meses.append(saidas_mes)
        entradas_meses.append(entradas_mes)
        entradas_meses_valor.append(entradas_mes_valor)
        preco_unitario_meses.append(preco_unitario_mes)
    
    for i in range(0, len(saidas_meses)):
        valor_saidas_meses.append(saidas_meses[i]*preco_unitario_meses[i])
        saldo_meses.append(entradas_meses[i]-saidas_meses[i])
    valor_saidas_ano = sum(valor_saidas_meses)
    saldo_ano =sum(saldo_meses)


    saidas_ano = nonetest(Abastecimento.objects.filter(data__year=year).aggregate(Sum('litros'))['litros__sum'])
    entradas_ano = nonetest(Entrada.objects.filter(data_entrega__year=year).aggregate(Sum('quantidade'))['quantidade__sum'])
    entradas_ano_valor = nonetest(Entrada.objects.filter(data_entrega__year=year).aggregate(Sum('preco_total'))['preco_total__sum'])
    preco_unitario_ano = nonetest(Entrada.objects.filter(data_entrega__year=year).aggregate(Avg('preco_unitario'))['preco_unitario__avg'])
    saldo_ano_anterior = Saldo.objects.get(ano=yearb) #coletar um específico objeto
    saldo_ano_anteriorv = Saldo.objects.filter(ano=yearb).aggregate(Sum('quantidade'))['quantidade__sum']
    saldo_acumulado_ano = float(entradas_ano) - float(saidas_ano) + float(saldo_ano_anteriorv)
   
    count = 0
    for i in saldo_meses:
        
        
        if count == 0:
            saldo_acumulado_meses.append(i + saldo_ano_anteriorv)

        else:
            saldo_acumulado_meses.append(i + saldo_acumulado_meses[count-1])
        count+=1
            
    return render(request, 'obras_ano.html', {'obras':obras, 
                                              'lista':lista, 
                                              'saidas_meses':saidas_meses, 
                                              'saidas_ano':saidas_ano, 
                                              'entradas_meses':entradas_meses, 
                                              'entradas_ano':entradas_ano,
                                              'entradas_meses_valor':entradas_meses_valor,
                                              'entradas_ano_valor':entradas_ano_valor,
                                              'preco_unitario_meses':preco_unitario_meses,
                                              'preco_unitario_ano':preco_unitario_ano,
                                              'valor_saidas_meses':valor_saidas_meses,
                                              'valor_saidas_ano':valor_saidas_ano,
                                              'saldo_meses':saldo_meses,
                                              'saldo_ano':saldo_ano,
                                              'yearb':yearb,
                                              'saldo_ano_anterior':saldo_ano_anterior,
                                              'saldo_acumulado_meses':saldo_acumulado_meses,
                                              'saldo_acumulado_ano':saldo_acumulado_ano,
                                              'grafico_vunit':g_vunit})

 else: return HttpResponse("<h1>Acesso Negado</h1>")
def importexcel(request):
    if request.method == 'POST':
        
        if 'excel' in request.FILES:
            excelfile = request.FILES['excel']
            workbook = openpyxl.load_workbook(excelfile)
            saidas = workbook['SAIDAS']
            entradas = workbook['ENTRADAS']
            transferencias = workbook['TRANSFERENCIAS']
            user_id = request.user

            #numeros:

            
            for i in entradas.iter_rows(min_row=3,values_only=True):
                
                ent = i[:10]
                print(ent)
                if ent[0] == None:
                        break
                else:
                
                        tanque = Tanque.objects.filter(prefixo=ent[0])[0]
                        obra = Obras.objects.filter(nome=ent[8])[0]
                        num_entrada = Entrada.objects.aggregate(Max('numero'))
                        num_entrada = num_entrada['numero__max']+1

                        entrada = Entrada(tanque=tanque,
                                            nota_fiscal=ent[4],
                                            fornecedor=ent[3],
                                            data_nf=ent[5],
                                            data_entrega=ent[1],
                                            obra=obra,
                                            quantidade=ent[2],
                                            preco_unitario=ent[6],
                                            preco_total=ent[7],
                                            colaborador=user_id,
                                            descricao=ent[9],
                                            numero = num_entrada)
                                            
                        entrada.save() 

            for i in transferencias.iter_rows(min_row=3, values_only=True):
                    
                    
                    tr = i[:7]
                    if tr[0] == None:
                        break
                    else:
                        tanque_fixo = Tanque.objects.get(prefixo=tr[0])
                        tanque_movel= Tanque.objects.get(prefixo=tr[1])


                        transferencia = Transferencia(fixo=tanque_fixo,
                                        movel=tanque_movel,
                                        contador_inicio=tr[2],
                                        contador_fim=tr[3],
                                        litros=tr[3]-tr[2],
                                        contador_comboio=tr[6],
                                        colaborador=user_id,
                                        data=tr[5])
                        transferencia.save()

            for i in saidas.iter_rows(min_row=3,values_only=True):
                    sds = i[:10]
                    print(sds)

                    if sds[0] == None:
                        break
                    else:
                        tanque_saida = Tanque.objects.get(prefixo=sds[0])
                        obra_saida = Obras.objects.get(nome=sds[2])
                        try:
                            equipamento_saida = Equipamentos.objects.get(prefixo=sds[3])
                            if sds[8] == None: lubrificacao = False
                            else: lubrificacao = True

                            if type(sds[7]) != int and type(sds[7]) != float:
                                horimetro = 0
                            else: horimetro =sds[7]

                        except:
                            print(sds[3], "erro")



                        num_saida = Abastecimento.objects.aggregate(Max('numero')) 
                        num_saida = (num_saida["numero__max"]+1)
                        print(num_saida)

                        saida = Abastecimento(litros=sds[5]-sds[4],
                                            contador_inicio=sds[4],
                                            contador_fim=sds[5],
                                            horimetro=horimetro,
                                            data=sds[1],
                                            tanque=tanque_saida,
                                            obra=obra_saida,
                                            equipamento=equipamento_saida,
                                            lubrificacao=lubrificacao,
                                            operador=sds[9],
                                            colaborador=user_id,
                                            status=True,
                                            observacao="",
                                            numero = num_saida
                                            )
                        
                        try:
                            saida.save()  
                            messages.add_message(request, constants.SUCCESS, "Arquivo importado com sucesso!" )  
                        except:
                            messages.add_message(request, constants.ERROR, "Erro na saída!" ) 

    else:
        pass
    return redirect('home/')




