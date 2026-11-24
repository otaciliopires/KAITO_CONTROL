from datetime import date, timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from autenticacao.models import Usuario
from ativos.models import Obras, Equipamentos
from .models import Tanque, Entrada, Abastecimento
from .views_relatorios import semanas_mes


class RelatoriosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ceq = Usuario.objects.create_user(username='relatorio_ceq', password='teste', status='c')
        cls.operador = Usuario.objects.create_user(username='relatorio_campo', password='teste', status='a')
        cls.usuario_obra = Usuario.objects.create_user(username='relatorio_obra', password='teste', status='o')
        cls.mestre = Usuario.objects.create_superuser(username='relatorio_mestre', password='teste')
        cls.tanque = Tanque.objects.create(prefixo='TQ-REL', capacidade=10000, estoque=0, tipo='F')
        cls.a = Obras.objects.create(nome='Água Branca', saldo=712.5)
        cls.b = Obras.objects.create(nome='Bravo', saldo=-35)
        cls.vazia = Obras.objects.create(nome='Sem movimento')
        cls.e1 = Equipamentos.objects.create(prefixo='EQ-01', descricao='Escavadeira')
        cls.e2 = Equipamentos.objects.create(prefixo='EQ-02', descricao='Caminhão')
        def entrada(obra, dia, litros, valor):
            Entrada.objects.create(obra=obra, tanque=cls.tanque, data_entrega=dia,
                data_nf=date(2026, 10, 28), quantidade=litros, preco_unitario=5,
                preco_total=valor, fornecedor='Fornecedor', nota_fiscal='NF-1', colaborador=cls.ceq)
        def saida(obra, equip, dia, litros, status=True):
            Abastecimento.objects.create(obra=obra, equipamento=equip, tanque=cls.tanque,
                data=dia, litros=litros, contador_inicio=0, contador_fim=litros,
                horimetro=100, operador='Operador', colaborador=cls.ceq, status=status)
        entrada(cls.a, date(2026,11,1), 1000.25, 5001.25)
        entrada(cls.a, date(2026,11,9), 200, 1000)
        entrada(cls.b, date(2026,11,30), 400, 2000)
        entrada(cls.a, date(2025,11,1), 9999, 49995)
        entrada(cls.a, date(2026,10,31), 9999, 49995)
        entrada(cls.a, date(2026,12,1), 9999, 49995)
        saida(cls.a, cls.e1, date(2026,11,1), 100.25)
        saida(cls.a, cls.e1, date(2026,11,2), 50)
        saida(cls.a, cls.e2, date(2026,11,30), 75, status=False)
        saida(cls.b, cls.e1, date(2026,11,2), 150)
        saida(None, cls.e2, date(2026,11,3), 25)
        saida(cls.a, cls.e1, date(2025,11,2), 9999)
        saida(cls.a, cls.e1, date(2026,12,1), 9999)

    def setUp(self):
        self.client.force_login(self.ceq)

    def get(self, **params):
        return self.client.get('/ceq/relatorio/', {'periodo':'2026-11', **params})

    def test_totais_mensais_separam_mes_e_ano(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        resumo = response.context['resumo']
        self.assertEqual(resumo['entradas'], Decimal('1600.25'))
        self.assertEqual(resumo['abastecimentos'], Decimal('400.25'))
        self.assertEqual(resumo['resultado'], Decimal('1200.00'))
        self.assertEqual(resumo['valor'], Decimal('8001.25'))
        self.assertEqual(resumo['notas'], 3)
        self.assertEqual(resumo['registros'], 5)
        self.assertEqual(response.context['obras_movimento'], 2)

    def test_todas_obras_incluem_zeradas_e_sem_vinculo(self):
        response = self.get()
        linhas = response.context['linhas_obras']
        self.assertEqual(len(linhas), 4)
        self.assertEqual(linhas[0]['nome'], 'Água Branca')
        self.assertEqual(linhas[-1]['nome'], 'Sem obra vinculada')
        self.assertEqual(sum(r['abastecimentos'] for r in linhas), response.context['resumo']['abastecimentos'])
        self.assertEqual(next(r for r in linhas if r['obra'] == self.vazia)['entradas'], 0)

    def test_semanas_nao_perdem_nem_duplicam_lancamentos(self):
        response = self.get()
        semanas = response.context['semanas']
        self.assertEqual(len(semanas), 6)
        self.assertEqual(semanas[0]['inicio'], date(2026,11,1))
        self.assertEqual(semanas[0]['fim'], date(2026,11,1))
        self.assertEqual(semanas[1]['inicio'], date(2026,11,2))
        self.assertEqual(sum(s['entradas'] for s in semanas), response.context['resumo']['entradas'])
        self.assertEqual(sum(s['abastecimentos'] for s in semanas), response.context['resumo']['abastecimentos'])
        self.assertEqual(sum(s['registros'] for s in semanas), 5)

    def test_obra_isola_lancamentos_e_preserva_saldo_cadastrado(self):
        response = self.get(visao='obra', obra=self.a.pk)
        self.assertEqual(response.status_code, 200)
        resumo = response.context['resumo']
        self.assertEqual(resumo['entradas'], Decimal('1200.25'))
        self.assertEqual(resumo['abastecimentos'], Decimal('225.25'))
        self.assertEqual(resumo['resultado'], Decimal('975'))
        self.assertEqual(response.context['obra_selecionada'].saldo, 712.5)
        self.assertEqual(len(response.context['notas']), 2)
        self.assertEqual(sum(s['abastecimentos'] for s in response.context['semanas']), Decimal('225.25'))

    def test_equipamentos_agrupados_somente_na_obra_e_no_mes(self):
        response = self.get(visao='obra', obra=self.a.pk)
        equipamentos = response.context['equipamentos']
        self.assertEqual(len(equipamentos), 2)
        self.assertEqual(equipamentos[0]['total'], Decimal('150.25'))
        self.assertEqual(equipamentos[0]['registros'], 2)
        self.assertEqual(equipamentos[1]['total'], Decimal('75'))
        self.assertAlmostEqual(sum(float(e['participacao']) for e in equipamentos), 100)
        self.assertEqual(sum(e['total'] for e in equipamentos), response.context['resumo']['abastecimentos'])

    def test_data_entrega_define_mes_da_entrada(self):
        response = self.get(visao='obra', obra=self.a.pk)
        self.assertEqual(response.context['resumo']['notas'], 2)
        self.assertEqual(response.context['notas'][0]['data_entrega'], date(2026,11,1))

    def test_filtros_invalidos_mostram_aviso_sem_erro(self):
        self.assertEqual(self.get(periodo='errado').status_code, 200)
        response = self.get(visao='obra', obra='inexistente')
        self.assertContains(response, 'Obra não encontrada')
        self.assertIsNone(response.context['obra_selecionada'])
        self.assertEqual(response.context['resumo']['entradas'], 0)
        self.assertEqual(self.get(periodo='9999-12').status_code, 200)

    def test_mes_vazio_e_obra_sem_movimento(self):
        response = self.get(periodo='2024-02', visao='obra', obra=self.vazia.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resumo']['entradas'], 0)
        self.assertTrue(response.context['sem_dados'])
        self.assertEqual(len(response.context['equipamentos']), 0)
        self.assertTrue(response.context['ultimo_link'])

    def test_consulta_nao_grava_nem_recalcula_saldo(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.get(visao='obra', obra=self.a.pk)
        self.assertEqual(response.status_code, 200)
        for q in queries:
            self.assertFalse(q['sql'].lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')), q['sql'])
        self.a.refresh_from_db()
        self.assertEqual(self.a.saldo, 712.5)

    def test_acesso_requer_login_e_perfil_ceq(self):
        self.client.logout()
        self.assertEqual(self.get().status_code, 302)
        self.client.force_login(self.usuario_obra)
        self.assertEqual(self.get().status_code, 403)
        self.client.force_login(self.operador)
        self.assertRedirects(self.get(), '/ceq/campo/', fetch_redirect_response=False)
        self.client.force_login(self.mestre)
        self.assertEqual(self.get().status_code, 200)

    def test_svg_usa_ponto_decimal_com_localizacao_portuguesa(self):
        response = self.get()
        from re import findall
        for valor in findall(r'(?:x|y|height|width)="([0-9.,]+)"', response.content.decode()):
            self.assertNotIn(',', valor)

    def test_semanas_cobrem_ano_bissexto_e_extremos_do_mes(self):
        for ano, mes in [(2024,2), (2026,3), (2026,12)]:
            import calendar
            inicio = date(ano,mes,1)
            fim = date(ano,mes,calendar.monthrange(ano,mes)[1])
            semanas = semanas_mes(inicio,fim)
            dias = []
            for s in semanas:
                atual = s['inicio']
                while atual <= s['fim']:
                    dias.append(atual)
                    atual += timedelta(days=1)
            self.assertEqual(len(dias), fim.day)
            self.assertEqual(len(dias), len(set(dias)))
            self.assertEqual(dias[0], inicio)
            self.assertEqual(dias[-1], fim)


    def test_pdf_usa_mes_e_obra_selecionados_e_duas_paginas(self):
        from io import BytesIO
        from pypdf import PdfReader
        response = self.client.get('/ceq/relatorio/pdf/', {'periodo': '2026-11', 'visao': 'obra', 'obra': self.a.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        pdf = PdfReader(BytesIO(response.content))
        self.assertEqual(len(pdf.pages), 2)
        texto = '\n'.join(page.extract_text() for page in pdf.pages)
        self.assertIn('Água Branca', texto)
        self.assertIn('Novembro de 2026', texto)
        self.assertIn('225,25 L', texto)
        self.assertIn('712,50 L', texto)
        for numero, pagina in enumerate(pdf.pages, 1):
            self.assertIn('Página '+str(numero), pagina.extract_text())
            self.assertAlmostEqual(float(pagina.mediabox.width), 595.2756, places=1)

    def test_pdf_exige_as_mesmas_permissoes_da_tela(self):
        self.client.logout()
        self.assertEqual(self.client.get('/ceq/relatorio/pdf/').status_code, 302)
        self.client.force_login(self.usuario_obra)
        self.assertEqual(self.client.get('/ceq/relatorio/pdf/').status_code, 403)

    def test_tabelas_longas_pdf_preservam_linhas_e_repetem_cabecalho(self):
        from io import BytesIO
        from pypdf import PdfReader
        from .relatorios_pdf import gerar_pdf
        from django.test import RequestFactory
        from .views_relatorios import dados_relatorio
        dados = dados_relatorio(RequestFactory().get('/ceq/relatorio/', {'periodo': '2026-11', 'visao': 'obra', 'obra': self.a.pk}))
        dados['equipamentos'] = [dict(equipamento__prefixo='EQ-PAG-{:03d}'.format(i),
            equipamento__descricao='Motor de teste {:03d}'.format(i), registros=1,
            total=Decimal('10'), participacao=Decimal('1.25'), ultimo=date(2026,11,30)) for i in range(80)]
        dados['notas'] = [dict(data_entrega=date(2026,11,1), nota_fiscal='NF-PAG-{:03d}'.format(i),
            fornecedor='Fornecedor de teste {:03d}'.format(i), quantidade=10, preco_total=50) for i in range(80)]
        dados['resumo'] = dict(entradas=Decimal('800'), abastecimentos=Decimal('800'), resultado=Decimal('0'),
            valor=Decimal('4000'), notas=80, registros=80)
        pdf = PdfReader(BytesIO(gerar_pdf(dados)))
        self.assertGreater(len(pdf.pages), 3)
        paginas = [pagina.extract_text() for pagina in pdf.pages]
        for texto in paginas[1:]:
            self.assertTrue('EQ-PAG-' in texto or 'NF-PAG-' in texto, 'Página de detalhes sem linhas da tabela: '+texto[:900])
        for i in range(80):
            codigo = 'EQ-PAG-{:03d}'.format(i)
            encontradas = [texto for texto in paginas if codigo in texto]
            self.assertEqual(len(encontradas), 1)
            self.assertIn('Motor de teste {:03d}'.format(i), encontradas[0])
            self.assertIn('Quantidade (L)', encontradas[0])
            self.assertIn('Descrição', encontradas[0])
            nota = 'NF-PAG-{:03d}'.format(i)
            encontradas = [texto for texto in paginas if nota in texto]
            self.assertEqual(len(encontradas), 1)
            self.assertIn('Fornecedor de teste {:03d}'.format(i), encontradas[0])
            self.assertIn('Nota fiscal', encontradas[0])
        self.assertEqual(sum(texto.count('TOTAL DA OBRA') for texto in paginas), 1)
        self.assertEqual(sum(texto.count('TOTAL DE ENTRADAS') for texto in paginas), 1)
