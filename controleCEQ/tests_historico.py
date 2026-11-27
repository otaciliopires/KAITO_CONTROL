from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch
from django.db import connection
from django.test import TestCase,RequestFactory
from django.test.utils import CaptureQueriesContext
from pypdf import PdfReader
from ativos.models import Obras,Equipamentos
from autenticacao.models import Usuario
from .models import Entrada,Abastecimento,Tanque
from .relatorio_historico import dados_historico


class HistoricoMensalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=Usuario.objects.create_user(username='historico_ceq',password='test',status='c')
        cls.obra_user=Usuario.objects.create_user(username='historico_obra',status='o')
        cls.master=Usuario.objects.create_superuser(username='historico_master',password='test',status='o')
        cls.a=Obras.objects.create(nome='Água Branca',saldo=1234.56)
        cls.b=Obras.objects.create(nome='Bravo',status='M')
        cls.c=Obras.objects.create(nome='Começou agora')
        cls.empty=Obras.objects.create(nome='Sem movimento')
        cls.tank=Tanque.objects.create(prefixo='HIST',tipo='F',capacidade=10000,estoque=789)
        cls.equip=Equipamentos.objects.create(prefixo='EQ-HIST')
        cls.entrada(cls.a,date(2024,12,1),1000)
        cls.entrada(cls.a,date(2025,4,30),200)
        cls.entrada(cls.c,date(2026,6,1),0)
        cls.saida(cls.a,date(2025,2,1),300)
        cls.saida(cls.b,date(2023,2,28),50)
        cls.saida(None,date(2025,9,1),77)

    @classmethod
    def entrada(cls,obra,dia,q):
        return Entrada.objects.create(numero=1,obra=obra,tanque=cls.tank,data_entrega=dia,
            data_nf=date(2026,11,27),nota_fiscal='HIST-NF',fornecedor='Fornecedor',quantidade=q,
            preco_unitario=5,preco_total=q*5,colaborador=cls.user)

    @classmethod
    def saida(cls,obra,dia,q):
        return Abastecimento.objects.create(numero=1,obra=obra,equipamento=cls.equip,tanque=cls.tank,
            data=dia,contador_inicio=0,contador_fim=q,horimetro=100,litros=q,operador='Operador',colaborador=cls.user)

    def setUp(self): self.client.force_login(self.user)
    def get(self,**params): return self.client.get('/ceq/relatorio/',{'visao':'historico',**params})

    def test_cada_obra_tem_o_proprio_intervalo_e_meses_vazios_no_meio(self):
        r=self.get()
        self.assertEqual(r.status_code,200)
        h={item['obra'].pk:item for item in r.context['historicos']}
        self.assertEqual(h[self.a.pk]['inicio'],date(2024,12,1))
        self.assertEqual(h[self.a.pk]['fim'],date(2025,4,1))
        self.assertEqual([m['mes'] for m in h[self.a.pk]['linhas']],[date(2024,12,1),date(2025,1,1),date(2025,2,1),date(2025,3,1),date(2025,4,1)])
        self.assertTrue(h[self.a.pk]['linhas'][1]['sem_movimento'])
        self.assertEqual(h[self.a.pk]['linhas'][1]['entradas'],0)
        self.assertEqual(h[self.b.pk]['meses'],1)
        self.assertEqual(h[self.b.pk]['inicio'],date(2023,2,1))
        self.assertEqual(h[self.c.pk]['meses'],1)
        self.assertEqual(h[self.c.pk]['fim'],date(2026,6,1))
        self.assertNotIn(self.empty.pk,h)
        self.assertIn(self.empty,r.context['obras_sem_movimento'])

    def test_totais_e_acumulado_sem_alterar_saldo_cadastrado(self):
        r=self.get(obra=self.a.pk)
        h=r.context['historicos'][0]
        self.assertEqual([m['acumulado'] for m in h['linhas']],[1000,1000,700,700,900])
        self.assertEqual(h['totais']['entradas'],1200)
        self.assertEqual(h['totais']['saidas'],300)
        self.assertEqual(h['totais']['resultado'],900)
        self.assertEqual(r.context['resumo']['notas'],2)
        self.a.refresh_from_db();self.tank.refresh_from_db()
        self.assertEqual(self.a.saldo,1234.56)
        self.assertEqual(self.tank.estoque,789)

    def test_saida_primeiro_e_entrada_depois_entre_anos(self):
        other=Obras.objects.create(nome='Somente depois')
        self.saida(other,date(2025,12,31),80)
        self.entrada(other,date(2026,2,1),20)
        h=self.get(obra=other.pk).context['historicos'][0]
        self.assertEqual([m['acumulado'] for m in h['linhas']],[-80,-80,-60])
        self.assertEqual(h['linhas'][1]['mes'],date(2026,1,1))

    def test_data_de_entrega_e_agrupamento_da_mesma_obra_no_mes(self):
        self.entrada(self.a,date(2025,4,1),25.5)
        self.saida(self.a,date(2025,4,1),10.25)
        self.saida(self.a,date(2025,4,30),5.25)
        h=self.get(obra=self.a.pk).context['historicos'][0]
        self.assertEqual(h['fim'],date(2025,4,1))
        self.assertEqual(h['linhas'][-1]['entradas'],Decimal('225.5'))
        self.assertEqual(h['linhas'][-1]['saidas'],Decimal('15.50'))
        self.assertEqual(h['linhas'][-1]['notas'],2)
        self.assertEqual(h['linhas'][-1]['registros'],2)

    def test_todas_as_obras_com_saida_sem_vinculo_identificada(self):
        r=self.get()
        self.assertEqual([h['obra'].nome for h in r.context['historicos']],['Água Branca','Bravo','Começou agora'])
        self.assertEqual(r.context['resumo']['entradas'],1200)
        self.assertEqual(r.context['resumo']['saidas'],350)
        self.assertEqual(r.context['resumo']['resultado'],850)
        self.assertEqual(r.context['sem_obra']['total'],77)
        self.assertContains(r,'Movimentação sem obra vinculada:')

    def test_selecao_vazia_e_id_invalido_nao_mostram_outras_obras(self):
        r=self.get(obra=self.empty.pk)
        self.assertEqual(r.context['historicos'],[])
        self.assertEqual(r.context['resumo']['entradas'],0)
        self.assertContains(r,'Nenhuma movimentação encontrada')
        r=self.get(obra='999999')
        self.assertTrue(r.context['aviso'])
        self.assertEqual(r.context['historicos'],[])
        r=self.get(obra='1 OR 1=1')
        self.assertTrue(r.context['aviso'])
        self.assertEqual(r.context['resumo']['saidas'],0)

    def test_consultas_em_lote_sem_gravar_no_banco(self):
        request=RequestFactory().get('/ceq/relatorio/',{'visao':'historico'})
        with CaptureQueriesContext(connection) as queries:
            dados_historico(request)
        self.assertLessEqual(len(queries),4)
        self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for q in queries))

    def test_abas_e_pdf_preservam_tipo_e_obra_sem_filtro_de_mes(self):
        r=self.get(obra=self.a.pk,periodo='2026-11')
        self.assertContains(r,'Histórico mensal')
        self.assertNotContains(r,'type="month"')
        self.assertIn('visao=historico',r.context['pdf_link'])
        self.assertIn('obra='+str(self.a.pk),r.context['pdf_link'])
        self.assertNotIn('periodo=',r.context['pdf_link'])
        self.assertEqual(r.context['historicos'][0]['inicio'],date(2024,12,1))
        self.assertContains(self.client.get('/ceq/relatorio/'),'visao=historico')

    def test_permissoes_da_tela_e_pdf(self):
        for url in ['/ceq/relatorio/?visao=historico','/ceq/relatorio/pdf/?visao=historico']:
            self.client.logout();self.assertEqual(self.client.get(url).status_code,302)
            self.client.force_login(self.obra_user);self.assertEqual(self.client.get(url).status_code,403)
            self.client.force_login(self.master);self.assertEqual(self.client.get(url).status_code,200)

    def test_pdf_tem_mesmos_meses_totais_e_apenas_obra_escolhida(self):
        with patch('socket.create_connection',side_effect=AssertionError('PDF sem recursos externos')):
            r=self.client.get('/ceq/relatorio/pdf/',{'visao':'historico','obra':self.a.pk})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r['Content-Disposition'].startswith('inline;'))
        text=' '.join(p.extract_text() for p in PdfReader(BytesIO(r.content)).pages)
        for expected in ['Água Branca','Dezembro / 2024','Janeiro / 2025','Abril / 2025','1.200,00','300,00','900,00']:
            self.assertIn(expected,text)
        self.assertNotIn('Bravo',text)

    def test_pdf_longo_repete_nome_e_colunas_sem_cortar_ultimo_mes_e_total(self):
        self.entrada(self.a,date(2010,1,1),1)
        r=self.client.get('/ceq/relatorio/pdf/',{'visao':'historico','obra':self.a.pk})
        pages=[p.extract_text() for p in PdfReader(BytesIO(r.content)).pages]
        self.assertGreater(len(pages),3)
        for text in pages:
            self.assertIn('Água Branca',text)
            self.assertIn('Acumulado (L)',' '.join(text.split()))
        self.assertIn('Abril / 2025',pages[-1])
        self.assertIn('TOTAL DA OBRA',pages[-1])
