from datetime import date
from io import BytesIO
from unittest.mock import patch
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from pypdf import PdfReader
from ativos.models import Obras
from autenticacao.models import Usuario
from .models import Entrada, Transferencia, Tanque


class MovimentosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=Usuario.objects.create_user(username='movimentos',status='c',password='test')
        cls.a=Obras.objects.create(nome='Água Branca')
        cls.b=Obras.objects.create(nome='Bravo')
        cls.vazia=Obras.objects.create(nome='Sem registros')
        cls.t1=Tanque.objects.create(prefixo='TQ-02',tipo='F',capacidade=1000,estoque=0)
        cls.t2=Tanque.objects.create(prefixo='TQ-10',tipo='F',capacidade=1000,estoque=0)
        cls.m1=Tanque.objects.create(prefixo='CM-01',tipo='M',capacidade=1000,estoque=0)
        cls.m2=Tanque.objects.create(prefixo='CM-02',tipo='M',capacidade=1000,estoque=0)
        cls.unused=Tanque.objects.create(prefixo='SEM-MOVIMENTO',tipo='F',capacidade=1000,estoque=0)
        for i,(obra,tanque,dia,q) in enumerate([(cls.a,cls.t1,date(2026,7,1),100),(cls.b,cls.t2,date(2026,7,10),200),(cls.a,cls.t2,date(2026,8,1),300)],1):
            Entrada.objects.create(numero=i,obra=obra,tanque=tanque,data_entrega=dia,data_nf=dia,
                nota_fiscal='NOTA-'+str(i),fornecedor='Fornecedor '+str(i),quantidade=q,preco_unitario=5,
                preco_total=q*5,colaborador=cls.user,descricao='Observacao '+str(i))
        for origem,destino,dia,q in [(cls.t1,cls.m1,date(2026,7,1),110),(cls.t2,cls.m2,date(2026,7,10),220),(cls.t1,cls.m2,date(2026,8,1),330)]:
            Transferencia.objects.create(fixo=origem,movel=destino,data=dia,litros=q,contador_inicio=0,contador_fim=q,colaborador=cls.user)

    def setUp(self):
        self.client.force_login(self.user)
        self.julho={'data_inicio':'2026-07-01','data_fim':'2026-07-31'}

    def test_obras_e_tanques_de_entradas_seguem_periodo_e_primeira_selecao(self):
        r=self.client.get('/ceq/entradas/opcoes/',dict(self.julho,obra=self.a.pk))
        self.assertEqual(r.status_code,200)
        groups=r.json()['grupos']
        self.assertEqual([o['id'] for o in groups['obra']],[self.a.pk,self.b.pk])
        self.assertEqual([o['id'] for o in groups['tanque']],[self.t1.pk])
        r=self.client.get('/ceq/entradas/opcoes/',{'data_inicio':'2026-07-10','data_fim':'2026-07-10','obra':self.a.pk})
        self.assertEqual(r.json()['grupos']['obra'],[{'id':self.b.pk,'label':self.b.nome}])
        self.assertEqual(r.json()['grupos']['tanque'],[{'id':self.t2.pk,'label':self.t2.prefixo}])
        page=self.client.get('/ceq/entradas/',dict(self.julho,obra=self.a.pk,tanque=self.t2.pk))
        self.assertEqual(page.context['pagina'].paginator.count,0)
        self.assertTrue(page.context['aviso'])

    def test_origens_e_destinos_transferencias_seguem_periodo_e_origem(self):
        r=self.client.get('/ceq/transferencias/opcoes/',dict(self.julho,tanque_fixo=self.t1.pk))
        groups=r.json()['grupos']
        self.assertEqual([o['id'] for o in groups['tanque_fixo']],[self.t1.pk,self.t2.pk])
        self.assertEqual([o['id'] for o in groups['tanque_movel']],[self.m1.pk])
        r=self.client.get('/ceq/transferencias/opcoes/',dict(self.julho,tanque_fixo=[self.t1.pk,self.t2.pk]))
        self.assertEqual({o['id'] for o in r.json()['grupos']['tanque_movel']},{self.m1.pk,self.m2.pk})

    def test_tabelas_totais_e_pdf_usam_mesmo_recorte(self):
        for tipo,params,total,extra in [('entradas',dict(self.julho,obra=self.a.pk),100,'NOTA-1'),('transferencias',dict(self.julho,tanque_fixo=self.t1.pk),110,'CM-01')]:
            with self.subTest(tipo=tipo):
                page=self.client.get('/ceq/'+tipo+'/',params)
                self.assertEqual(page.context['total'],total)
                self.assertEqual(page.context['pagina'].paginator.count,1)
                self.assertContains(page,'id="movimentos-filtros"')
                self.assertNotContains(page,'basicModal')
                self.assertContains(page,'movimentos_filtros.js')
                with patch('socket.create_connection',side_effect=AssertionError('No external resources')):
                    pdf=self.client.get('/ceq/'+tipo+'_pdf/',params)
                self.assertEqual(pdf.status_code,200)
                self.assertTrue(pdf['Content-Disposition'].startswith('inline;'))
                text=' '.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
                self.assertIn(str(total)+',00 L',text)
                self.assertIn(extra,text)
                self.assertNotIn('NOTA-2',text)
                if tipo=='entradas':
                    self.assertEqual(page.context['valor'],500)
                    self.assertIn('R$ 500,00',text)

    def test_filtros_vazios_sem_registros_e_links_anteriores(self):
        for tipo in ('entradas','transferencias'):
            page=self.client.get('/ceq/'+tipo+'/')
            self.assertEqual(page.context['pagina'].paginator.count,3)
            self.assertEqual(page.context['total'],600 if tipo=='entradas' else 660)
            empty={'data_inicio':'2020-01-01','data_fim':'2020-01-01'}
            self.assertEqual(self.client.get('/ceq/'+tipo+'/',empty).context['pagina'].paginator.count,0)
            groups=self.client.get('/ceq/'+tipo+'/opcoes/',empty).json()['grupos']
            self.assertTrue(all(not values for values in groups.values()))
            pdf=self.client.get('/ceq/'+tipo+'_pdf/',empty)
            self.assertEqual(pdf.status_code,200)
            self.assertIn('Nenhum',' '.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages))
        legacy=self.client.get('/ceq/entradas_pdf/',{'data_inicio1':'2026-07-01','data_fim1':'2026-07-31','obra':str(self.a.pk)+','+str(self.b.pk)})
        self.assertEqual(legacy.status_code,200)
        self.assertIn('300,00 L',PdfReader(BytesIO(legacy.content)).pages[0].extract_text())

    def test_permissoes_validacao_e_consultas_sem_escrita(self):
        for tipo in ('entradas','transferencias'):
            for endpoint in ('/','/opcoes/','_pdf/'):
                url='/ceq/'+tipo+endpoint
                self.assertEqual(self.client.get(url,{'data_inicio':'invalid'}).status_code,400)
                self.assertEqual(self.client.get(url,{'data_inicio':'2026-08-01','data_fim':'2026-07-01'}).status_code,400)
                with CaptureQueriesContext(connection) as captured:
                    self.assertEqual(self.client.get(url,self.julho).status_code,200)
                self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for q in captured))
        user=Usuario.objects.create_user(username='negado',status='o')
        self.client.force_login(user)
        for tipo in ('entradas','transferencias'):
            for endpoint in ('/','/opcoes/','_pdf/'):
                self.assertEqual(self.client.get('/ceq/'+tipo+endpoint).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get('/ceq/entradas/opcoes/').status_code,302)

    def test_paginacao_preserva_filtros_e_opcoes_abrangem_todas_paginas(self):
        original=Entrada.objects.first()
        for i in range(101):
            original.pk=None
            original.numero=1000+i
            original.save()
        r=self.client.get('/ceq/entradas/',dict(self.julho,page=2,obra=[self.a.pk,self.b.pk]))
        self.assertEqual(r.context['pagina'].paginator.count,103)
        self.assertEqual(len(r.context['linhas']),3)
        self.assertNotIn('page=',r.context['querystring'])
        self.assertEqual(len(r.context['grupos'][0]['opcoes']),2)
        self.assertEqual(r.context['total'],10400)

    def test_pdf_longo_com_total_na_mesma_pagina_do_ultimo_lancamento(self):
        from copy import copy
        from django.http import QueryDict
        from django.utils import timezone
        from .views_movimentos import CONFIG,consultar,celulas
        from .movimentos_pdf import gerar_pdf
        for tipo in ('entradas','transferencias'):
            dados=consultar(QueryDict(''),tipo)
            original=dados['qs'].first()
            rows=[]
            for i in range(130):
                r=copy(original)
                if tipo=='entradas':r.numero=900000+i
                else:r.pk=900000+i
                rows.append(r)
            pdf=gerar_pdf(tipo,CONFIG[tipo],dados,rows,celulas,timezone.localtime())
            pages=[p.extract_text() for p in PdfReader(BytesIO(pdf)).pages]
            self.assertGreater(len(pages),2)
            for page in pages:
                self.assertIn('Quantidade (L)',' '.join(page.split()))
            for i in range(130):
                self.assertTrue(any(str(900000+i) in page for page in pages))
            self.assertIn('900129',pages[-1])
            self.assertIn('TOTAL GERAL',pages[-1])
