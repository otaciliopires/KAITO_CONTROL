from datetime import date
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from autenticacao.models import Usuario
from ativos.models import Obras, Equipamentos
from .colunas_saidas import COLUNAS
from .models import Abastecimento, Tanque


class SaidasFiltrosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=Usuario.objects.create_user(username='ceq_filtro',password='teste',status='c')
        cls.obra_user=Usuario.objects.create_user(username='obra_filtro',password='teste',status='o')
        cls.campo_user=Usuario.objects.create_user(username='campo_filtro',password='teste',status='a')
        cls.mestre=Usuario.objects.create_superuser(username='mestre_filtro',password='teste',status='o')
        cls.tanque=Tanque.objects.create(prefixo='TQ-FILTRO',capacidade=10000,estoque=0,tipo='F')
        cls.a=Obras.objects.create(nome='Água Branca')
        cls.b=Obras.objects.create(nome='Bravo')
        cls.vazia=Obras.objects.create(nome='Obra vazia')
        cls.e1=Equipamentos.objects.create(prefixo='EQ-01',descricao='Escavadeira')
        cls.e2=Equipamentos.objects.create(prefixo='EQ-02',descricao='Caminhão')
        cls.shared=Equipamentos.objects.create(prefixo='EQ-03',descricao='Compartilhado')
        cls.old=Equipamentos.objects.create(prefixo='EQ-04',descricao='Outro mês')
        cls.unused=Equipamentos.objects.create(prefixo='EQ-99',descricao='Nunca abastecido')
        registros=[(cls.a,cls.e1,date(2026,7,1),100),(cls.a,cls.shared,date(2026,7,10),20),
                   (cls.b,cls.e2,date(2026,7,1),200),(cls.b,cls.shared,date(2026,7,11),30),
                   (cls.a,cls.old,date(2026,6,30),300),(cls.a,cls.e1,date(2026,8,1),150),
                   (None,cls.shared,date(2026,7,2),40)]
        cls.rows=[]
        for i,(obra,equip,dia,litros) in enumerate(registros,1):
            cls.rows.append(Abastecimento.objects.create(numero=i,obra=obra,equipamento=equip,tanque=cls.tanque,
                data=dia,litros=litros,contador_inicio=0,contador_fim=litros,horimetro=100,
                operador='Operador '+str(i),colaborador=cls.user))

    def setUp(self):
        self.client.force_login(self.user)
        self.julho={'data_inicio':'2026-07-01','data_fim':'2026-07-31'}

    def opcoes(self,**params):
        response=self.client.get('/ceq/saidas/equipamentos/',params)
        self.assertEqual(response.status_code,200)
        return {item['id'] for item in response.json()['equipamentos']}

    def test_lista_de_equipamentos_respeita_obra_e_datas(self):
        self.assertEqual(self.opcoes(**self.julho,obra=self.a.pk),{self.e1.pk,self.shared.pk})
        self.assertEqual(self.opcoes(**self.julho,obra=self.b.pk),{self.e2.pk,self.shared.pk})
        self.assertEqual(self.opcoes(obra=self.a.pk),{self.e1.pk,self.shared.pk,self.old.pk})

    def test_datas_sozinhas_atualizam_equipamentos_e_limites_inclusivos(self):
        params={'data_inicio':'2026-07-01','data_fim':'2026-07-01'}
        self.assertEqual(self.opcoes(**params),{self.e1.pk,self.e2.pk})
        response=self.client.get('/ceq/saidas/',params)
        self.assertEqual(response.context['saidas'].paginator.count,2)
        self.assertEqual(response.context['total_saidas'],300)

    def test_selecao_multipla_de_obras_usa_uniao_dos_equipamentos(self):
        self.assertEqual(self.opcoes(**self.julho,obra=[self.a.pk,self.b.pk]),{self.e1.pk,self.e2.pk,self.shared.pk})

    def test_equipamento_escolhido_nao_restringe_as_outras_opcoes(self):
        self.assertEqual(self.opcoes(**self.julho,obra=self.a.pk,equipamento=self.e1.pk),{self.e1.pk,self.shared.pk})
        response=self.client.get('/ceq/saidas/',dict(self.julho,equipamento=self.e1.pk))
        self.assertEqual(response.context['saidas'].paginator.count,1)
        self.assertEqual({e.pk for e in response.context['equipamentos']},{self.e1.pk,self.e2.pk,self.shared.pk})
        self.assertEqual(response.context['total_saidas'],100)

    def test_equipamentos_sem_abastecimento_nao_aparecem(self):
        self.assertNotIn(self.unused.pk,self.opcoes())
        response=self.client.get('/ceq/saidas/equipamentos/',dict(self.julho,obra=self.vazia.pk))
        self.assertNotIn(self.vazia.pk,{o['id'] for o in response.json()['obras']})
        self.assertEqual(self.client.get('/ceq/saidas/',dict(self.julho,obra=self.vazia.pk)).context['saidas'].paginator.count,0)

    def test_selecao_incompativel_nao_amplia_resultados(self):
        response=self.client.get('/ceq/saidas/',dict(self.julho,obra=self.a.pk,equipamento=self.e2.pk))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['saidas'].paginator.count,0)
        self.assertEqual(response.context['total_saidas'],0)
        self.assertTrue(response.context['aviso_filtro'])
        self.assertNotIn(self.e2.pk,{e.pk for e in response.context['equipamentos']})

    def test_sem_filtros_total_e_tabela_consideram_os_mesmos_lancamentos(self):
        response=self.client.get('/ceq/saidas/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['saidas'].paginator.count,7)
        self.assertEqual(response.context['total_saidas'],840)
        self.assertIn(self.rows[-1],response.context['saidas'].object_list)

    def test_filtros_sao_exibidos_na_pagina_sem_modal(self):
        response=self.client.get('/ceq/saidas/',dict(self.julho,obra=self.a.pk))
        self.assertContains(response,'id="saidas-filtros"')
        self.assertContains(response,'id="data-inicio"')
        self.assertContains(response,'data-equipamentos-url="/ceq/saidas/equipamentos/"')
        self.assertNotContains(response,'id="basicModal"')
        self.assertNotContains(response,'data-bs-toggle="modal"')
        self.assertEqual([obra.nome for obra in response.context['obras']],['Água Branca','Bravo'])

    def test_datas_invalidas_e_intervalo_invertido_nao_geram_erro_500(self):
        for params in [{'data_inicio':'inválido'}, {'data_inicio':'2026-07-31','data_fim':'2026-07-01'}, {'obra':'abc'}]:
            with self.subTest(params=params):
                response=self.client.get('/ceq/saidas/',params)
                self.assertEqual(response.status_code,400)
                self.assertEqual(response.context['saidas'].paginator.count,0)
                self.assertEqual(self.client.get('/ceq/saidas/equipamentos/',params).status_code,400)

    def test_api_ignora_equipamento_pois_filtra_apenas_pelos_filtros_primarios(self):
        self.assertEqual(self.opcoes(**self.julho,obra=self.a.pk,equipamento='inválido'),{self.e1.pk,self.shared.pk})

    def test_opcoes_consideram_todas_as_paginas(self):
        outro=Equipamentos.objects.create(prefixo='EQ-05')
        novos=[Abastecimento(numero=1000+i,obra=self.a,equipamento=self.e1,tanque=self.tanque,
            data=date(2026,7,1),litros=1,contador_inicio=0,contador_fim=1,horimetro=1,
            operador='Paginação',colaborador=self.user) for i in range(101)]
        novos.append(Abastecimento(numero=0,obra=self.a,equipamento=outro,tanque=self.tanque,
            data=date(2026,7,1),litros=1,contador_inicio=0,contador_fim=1,horimetro=1,
            operador='Fora da primeira página',colaborador=self.user))
        Abastecimento.objects.bulk_create(novos)
        response=self.client.get('/ceq/saidas/',dict(self.julho,obra=self.a.pk,equipamento=[]))
        self.assertEqual(len(response.context['saidas'].object_list),100)
        self.assertEqual(response.context['saidas'].paginator.count,104)
        self.assertIn(outro.pk,{e.pk for e in response.context['equipamentos']})
        self.assertEqual(response.context['total_saidas'],222)
        self.assertNotIn('page=',response.context['querystring'])

    def test_pdf_usa_os_mesmos_filtros_e_aceita_links_csv_anteriores(self):
        params=dict(self.julho,obra=str(self.a.pk)+','+str(self.b.pk),equipamento=str(self.shared.pk))
        with patch('controleCEQ.views_saidas.gerar_saidas_pdf',return_value=b'%PDF-test') as render:
            response=self.client.get('/ceq/saidas_pdf/',params)
        self.assertEqual(response.status_code,200)
        registros=render.call_args[0][0]
        self.assertEqual({r['numero'] for r in registros},{self.rows[1].numero,self.rows[3].numero})
        self.assertEqual(sum(r['litros'] for r in registros),50)

    def test_pdf_sem_equipamento_selecionado_inclui_todos_no_recorte(self):
        params=dict(self.julho,obra=[self.a.pk,self.b.pk])
        with patch('controleCEQ.views_saidas.gerar_saidas_pdf',return_value=b'%PDF-test') as render:
            self.assertEqual(self.client.get('/ceq/saidas_pdf/',params).status_code,200)
        self.assertEqual(len(render.call_args[0][0]),4)
        self.assertEqual(sum(r['litros'] for r in render.call_args[0][0]),350)

    def test_permissoes_api_privada_e_ausencia_de_gravacoes(self):
        with CaptureQueriesContext(connection) as queries:
            response=self.client.get('/ceq/saidas/',dict(self.julho,obra=self.a.pk))
        self.assertEqual(response.status_code,200)
        self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for q in queries))
        api=self.client.get('/ceq/saidas/equipamentos/',self.julho)
        self.assertIn('no-store',api['Cache-Control'])
        self.assertEqual(self.client.post('/ceq/saidas/equipamentos/').status_code,405)
        self.client.logout()
        self.assertEqual(self.client.get('/ceq/saidas/').status_code,302)
        self.assertEqual(self.client.get('/ceq/saidas/equipamentos/').status_code,302)
        self.client.force_login(self.obra_user)
        self.assertEqual(self.client.get('/ceq/saidas/').status_code,403)
        self.assertEqual(self.client.get('/ceq/saidas/equipamentos/').status_code,403)
        self.assertEqual(self.client.get('/ceq/saidas_pdf/').status_code,403)
        self.client.force_login(self.mestre)
        self.assertEqual(self.client.get('/ceq/saidas/').status_code,200)

    def test_obras_disponiveis_respeitam_datas_sem_limitar_a_propria_selecao(self):
        params={'data_inicio':'2026-07-10','data_fim':'2026-07-10','obra':self.b.pk}
        api=self.client.get('/ceq/saidas/equipamentos/',params)
        self.assertEqual(api.json()['obras'],[{'id':self.a.pk,'nome':self.a.nome}])
        # The stale work selection is cleared; equipment follows the remaining date scope.
        self.assertEqual({e['id'] for e in api.json()['equipamentos']},{self.shared.pk})
        page=self.client.get('/ceq/saidas/',params)
        self.assertEqual([o.pk for o in page.context['obras']],[self.a.pk])
        self.assertEqual(page.context['saidas'].paginator.count,0)
        self.assertTrue(page.context['aviso_filtro'])

    def test_obras_sem_abastecimento_e_periodo_vazio(self):
        api=self.client.get('/ceq/saidas/equipamentos/')
        self.assertEqual([o['id'] for o in api.json()['obras']],[self.a.pk,self.b.pk])
        params={'data_inicio':'2026-07-02','data_fim':'2026-07-02'}
        api=self.client.get('/ceq/saidas/equipamentos/',params)
        self.assertEqual(api.json()['obras'],[])
        self.assertEqual({e['id'] for e in api.json()['equipamentos']},{self.shared.pk})
        params={'data_inicio':'2020-01-01','data_fim':'2020-01-02'}
        api=self.client.get('/ceq/saidas/equipamentos/',params)
        self.assertEqual(api.json(),{'obras':[],'equipamentos':[]})

    def test_pdf_real_tem_filtros_total_e_lubrificacao_sem_consultar_recursos_externos(self):
        from io import BytesIO
        from pypdf import PdfReader
        with patch('socket.create_connection', side_effect=AssertionError('PDF must not access the network')):
            response=self.client.get('/ceq/saidas_pdf/',dict(self.julho,obra=self.a.pk))
        self.assertEqual(response.status_code,200)
        reader=PdfReader(BytesIO(response.content))
        text=' '.join(page.extract_text() for page in reader.pages)
        self.assertIn('120,00 L',text)
        self.assertIn(self.a.nome,text)
        self.assertIn('01/07/2026 a 31/07/2026',text)
        self.assertIn('Lubrificação',text)
        self.assertNotIn('Bravo',text)
        self.assertGreater(float(reader.pages[0].mediabox.width),float(reader.pages[0].mediabox.height))

    def test_pdf_longo_repete_cabecalho_nao_separa_lancamento_e_total(self):
        from io import BytesIO
        from pypdf import PdfReader
        from django.utils import timezone
        from .saidas_pdf import gerar_saidas_pdf, FIELDS
        from .views_saidas import consulta_saidas
        from django.http import QueryDict
        consulta=consulta_saidas(QueryDict(''))
        base=consulta['saidas'].values(*FIELDS).first()
        rows=[]
        for i in range(180):
            row=dict(base,numero=900000+i,operador='OperadorTeste'+str(i))
            row['obra__nome']='Obra extensa para verificar quebra de linha e continuidade do documento'
            rows.append(row)
        reader=PdfReader(BytesIO(gerar_saidas_pdf(rows,consulta,timezone.localtime())))
        pages=[page.extract_text() for page in reader.pages]
        self.assertGreater(len(pages),2)
        for page in pages:
            self.assertIn('Equipamento',page)
            self.assertIn('Quantidade (L)',' '.join(page.split()))
        for i in range(180):
            self.assertTrue(any(str(900000+i) in page and 'OperadorTeste'+str(i) in page for page in pages))
        self.assertIn('900179',pages[-1])
        self.assertIn('TOTAL GERAL',pages[-1])

    def test_entradas_pdf_abre_para_visualizacao(self):
        response=self.client.get('/ceq/entradas_pdf/')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response['Content-Disposition'].startswith('inline;'))

    def test_transferencias_pdf_preserva_filtros_e_abre_inline(self):
        from io import BytesIO
        from pypdf import PdfReader
        from .models import Transferencia
        destino=Tanque.objects.create(prefixo='CM-TESTE',tipo='M',capacidade=1000,estoque=0)
        for dia,litros in [(date(2026,7,1),123),(date(2026,8,1),456)]:
            Transferencia.objects.create(fixo=self.tanque,movel=destino,litros=litros,data=dia,
                contador_inicio=0,contador_fim=litros,colaborador=self.user)
        params=dict(self.julho,tanque_fixo=self.tanque.pk,tanque_movel=destino.pk)
        response=self.client.get('/ceq/transferencias_pdf/',params)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response['Content-Disposition'].startswith('inline;'))
        text=' '.join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
        self.assertIn('123,00 L',text)
        self.assertNotIn('456,00',text)
        self.assertIn('CM-TESTE',text)
        page=self.client.get('/ceq/transferencias/',params)
        self.assertEqual(page.context['transferencias'].paginator.count,1)
        self.assertContains(page,'target="_blank"')
        self.assertIn('tanque_movel=',page.context['querystring'])
        self.assertEqual(self.client.get('/ceq/transferencias_pdf/',{'data_inicio':'invalid'}).status_code,400)
        self.client.force_login(self.obra_user)
        self.assertEqual(self.client.get('/ceq/transferencias_pdf/').status_code,403)

    def test_colunas_selecionadas_preservadas_no_html_e_consulta(self):
        params=dict(self.julho,coluna=['obra','quantidade'],personalizar_colunas='1')
        response=self.client.get('/ceq/saidas/',params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['colunas_visiveis'],['obra','quantidade'])
        self.assertEqual(response.context['total_saidas'],390)
        self.assertEqual(response.context['saidas'].paginator.count,5)
        self.assertIn('coluna=obra',response.context['querystring'])
        self.assertIn('coluna=quantidade',response.context['querystring'])
        self.assertContains(response,'data-coluna="operador" hidden')
        self.assertContains(response,'form="saidas-filtros"')
        self.assertContains(response,'id="colunas-relatorio"')

    def test_pdf_respeita_colunas_e_descricao_abaixo_do_equipamento(self):
        from io import BytesIO
        from pypdf import PdfReader
        for selected in [['data','quantidade'],['descricao'],['equipamento'],['equipamento','descricao']]:
            params=dict(self.julho,obra=self.a.pk,coluna=selected,personalizar_colunas='1')
            response=self.client.get('/ceq/saidas_pdf/',params)
            self.assertEqual(response.status_code,200)
            text=' '.join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
            self.assertNotIn('Operador / motorista',text)
            self.assertNotIn('Lubrificação',text)
            self.assertNotIn('Horímetro / km',text)
            self.assertIn('120,00 L',text)
            if set(selected)=={'equipamento','descricao'}:
                self.assertIn('Equipamento / descrição',text)
                self.assertEqual(text.count('Escavadeira'),1)
                positions={}
                def position(t,cm,tm,font,size):
                    if t.strip() in ('EQ-01','Escavadeira'):
                        positions[t.strip()]=(tm[4],tm[5])
                PdfReader(BytesIO(response.content)).pages[0].extract_text(visitor_text=position)
                self.assertEqual(positions['EQ-01'][0],positions['Escavadeira'][0])
                self.assertGreater(positions['EQ-01'][1],positions['Escavadeira'][1])
            elif 'descricao' in selected:
                self.assertIn('Escavadeira',text)
                self.assertNotIn('EQ-01',text)
            elif 'equipamento' in selected:
                self.assertIn('EQ-01',text)
                self.assertNotIn('Escavadeira',text)
            else:
                self.assertNotIn('Escavadeira',text)
                self.assertIn('Quantidade (L)',' '.join(text.split()))

    def test_coluna_invalida_ou_nenhuma_selecao_da_erro_controlado(self):
        for params in [{'personalizar_colunas':'1'},{'coluna':'inexistente'},{'coluna':['obra','<script>']}]:
            self.assertEqual(self.client.get('/ceq/saidas/',params).status_code,400)
            self.assertEqual(self.client.get('/ceq/saidas_pdf/',params).status_code,400)
        response=self.client.get('/ceq/saidas/',{'coluna':['obra','obra']})
        self.assertEqual(response.context['colunas_visiveis'],['obra'])
        self.assertEqual(self.client.get('/ceq/saidas/').context['colunas_visiveis'],[c['id'] for c in COLUNAS])
