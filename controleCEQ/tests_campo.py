import json
from uuid import uuid4
from django.test import TestCase, Client, override_settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from autenticacao.models import Usuario
from ativos.models import Obras, Equipamentos
from .models import Tanque, Abastecimento, ReciboAbastecimentoCampo


class CampoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tanque = Tanque.objects.create(prefixo='CAMPO', capacidade=4000, estoque=0, tipo='M')
        cls.outro = Tanque.objects.create(prefixo='OUTRO', capacidade=4000, estoque=0, tipo='F')
        cls.obra = Obras.objects.create(nome='Obra campo')
        cls.equip = Equipamentos.objects.create(prefixo='EQ-CAMPO')
        cls.user = Usuario.objects.create_user(username='abastecedor_teste', password='teste', status='a', tanque_abastecimento=cls.tanque)
        cls.mestre = Usuario.objects.create_superuser(username='mestre_teste', password='teste')
        cls.ceq = Usuario.objects.create_user(username='ceq_teste', password='teste', status='c')

    def setUp(self):
        self.client.force_login(self.user)
        self.payload = dict(id=str(uuid4()), usuario_id=self.user.pk, tanque_id=self.tanque.pk,
            obra_id=self.obra.pk, equipamento_id=self.equip.pk, data='2026-10-27',
            contador_inicio='1.000,50', contador_fim='1.125,75', horimetro='400,5',
            operador='Operador', lubrificacao=True, observacao='Campo', registrado_em=timezone.now().isoformat())

    def post(self, payload=None):
        return self.client.post('/ceq/campo/api/enviar/', data=json.dumps(payload or self.payload), content_type='application/json')

    def test_sincroniza_calcula_litros_saldos_e_lubrificacao(self):
        self.assertEqual(self.post().status_code, 200)
        a = Abastecimento.objects.get()
        self.assertEqual(a.litros, 125.25)
        self.assertTrue(a.lubrificacao)
        self.assertEqual(a.colaborador, self.user)
        self.obra.refresh_from_db(); self.tanque.refresh_from_db()
        self.assertEqual(self.obra.saldo, -125.25)
        self.assertEqual(self.tanque.estoque, -125.25)
        self.assertEqual(ReciboAbastecimentoCampo.objects.count(), 1)

    def test_assinatura_preservada_e_reenvio_idempotente(self):
        self.payload['assinatura'] = {'versao': 1, 'tracos': [[[0.1, 0.2], [0.3, 0.4], [0.8, 0.3]]]}
        resposta = self.post()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Abastecimento.objects.get().assinatura, self.payload['assinatura'])
        self.assertEqual(self.post().json(), resposta.json())
        self.assertEqual(Abastecimento.objects.count(), 1)

    def test_assinatura_invalida_nao_cria_abastecimento(self):
        for assinatura in [{'versao': 1, 'tracos': [[[0, 0], [2, 1]]]},
                           {'versao': 1, 'tracos': [[[False, 0], [1, 1]]]},
                           {'versao': 1, 'tracos': [[[0, 0]]]},
                           {'versao': 1, 'tracos': [[[0, 0], [1, 1]]] * 65},
                           'data:image/svg+xml,invalid']:
            with self.subTest(assinatura=assinatura):
                self.payload['assinatura'] = assinatura
                self.assertEqual(self.post().status_code, 400)
                self.assertFalse(Abastecimento.objects.exists())

    def test_resposta_perdida_reenvio_nao_duplica(self):
        a = self.post().json()
        b = self.post().json()
        self.assertEqual(a, b)
        self.assertEqual(Abastecimento.objects.count(), 1)
        self.assertEqual(ReciboAbastecimentoCampo.objects.count(), 1)

    def test_id_reutilizado_com_dados_diferentes_bloqueia(self):
        self.post(); self.payload['operador'] = 'Alterado'
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(Abastecimento.objects.count(), 1)

    def test_outro_tanque_e_outro_usuario_bloqueados(self):
        self.payload['tanque_id'] = self.outro.pk
        self.assertEqual(self.post().status_code, 403)
        self.payload['tanque_id'] = self.tanque.pk
        self.payload['usuario_id'] = self.mestre.pk
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse(Abastecimento.objects.exists())

    def test_catalogo_so_mostra_tanque_autorizado(self):
        res = self.client.get('/ceq/campo/api/cadastros/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([t['id'] for t in res.json()['tanques']], [self.tanque.pk])
        self.assertIn('no-store', res.headers['Cache-Control'])

    def test_restricao_paginas_admin_api_e_post_legado(self):
        for path in ('/admin/', '/ceq/home/', '/ceq/operacoes/', '/estoque/', '/medicao/painel/'):
            self.assertRedirects(self.client.get(path), '/ceq/campo/', fetch_redirect_response=False)
        self.assertEqual(self.client.post('/ceq/operacoes/', {'form_saidas': '1'}).status_code, 403)
        self.assertEqual(self.client.get('/api/equipamentos/').status_code, 403)

    def test_sessao_expirada_e_usuario_sem_permissao(self):
        self.client.logout()
        self.assertEqual(self.post().status_code, 401)
        self.client.force_login(self.ceq)
        self.assertEqual(self.post().status_code, 403)

    def test_remocao_do_tanque_bloqueia_envio_pendente(self):
        self.user.tanque_abastecimento = self.outro; self.user.save()
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse(Abastecimento.objects.exists())

    def test_inativo_nao_sincroniza(self):
        self.user.is_active = False; self.user.save()
        self.assertEqual(self.post().status_code, 401)

    def test_valores_invalidos_nao_criam_registros(self):
        for inicio, fim in [('100', '90'), ('10', '10'), ('NaN', '20'), ('-1', '20'), ('0', 'Infinity')]:
            self.payload['contador_inicio'], self.payload['contador_fim'] = inicio, fim
            self.assertEqual(self.post().status_code, 400)
        self.assertFalse(Abastecimento.objects.exists())
        self.assertFalse(ReciboAbastecimentoCampo.objects.exists())

    def test_cadastro_inexistente_reverte_toda_transacao(self):
        self.payload['equipamento_id'] = 999999
        self.assertEqual(self.post().status_code, 400)
        self.assertFalse(Abastecimento.objects.exists())
        self.assertFalse(ReciboAbastecimentoCampo.objects.exists())

    def test_envio_atrasado_nao_regride_contador(self):
        self.tanque.contador = 9000; self.tanque.save()
        self.post(); self.tanque.refresh_from_db()
        self.assertEqual(self.tanque.contador, 9000)

    def test_csrf_exigido_e_token_dos_cadastros_funciona(self):
        c = Client(enforce_csrf_checks=True); c.force_login(self.user)
        self.assertEqual(c.post('/ceq/campo/api/enviar/', data=json.dumps(self.payload), content_type='application/json').status_code, 403)
        token = c.get('/ceq/campo/api/cadastros/').json()['csrf']
        self.assertEqual(c.post('/ceq/campo/api/enviar/', data=json.dumps(self.payload), content_type='application/json', HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_model_exige_tanque_e_sem_admin(self):
        self.user.tanque_abastecimento = None
        with self.assertRaises(ValidationError): self.user.full_clean()
        self.user.tanque_abastecimento = self.tanque; self.user.is_staff = True
        with self.assertRaises(ValidationError): self.user.full_clean()

    def test_login_encaminha_abastecedor_para_campo(self):
        self.client.logout()
        res = self.client.post('/auth/login/', {'username': self.user.username, 'password': 'teste'})
        self.assertRedirects(res, '/ceq/campo/', fetch_redirect_response=False)

    def test_shell_publico_sem_dados_e_worker_limitado(self):
        self.client.logout()
        html = self.client.get('/ceq/campo/').content.decode()
        self.assertNotIn(self.user.username, html)
        self.assertNotIn(self.obra.nome, html)
        self.assertNotIn('cdn.', html)
        worker = self.client.get('/ceq/campo/sw.js')
        self.assertEqual(worker.status_code, 200)
        self.assertNotIn('/auth/login/', worker.content.decode())

    def test_mestre_cadastra_perfil_e_tanque_no_admin(self):
        self.client.force_login(self.mestre)
        res = self.client.get('/admin/autenticacao/usuario/add/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'name="status"')
        self.assertContains(res, 'Abastecedor (campo)')
        self.assertContains(res, 'name="tanque_abastecimento"')
        from django.contrib import admin
        form_class = admin.site._registry[Usuario].get_form(res.wsgi_request)
        values = dict(username='novo_campo',password1='Campo-Temporario-487!',password2='Campo-Temporario-487!',status='a')
        form = form_class(data=values)
        self.assertFalse(form.is_valid())
        self.assertIn('tanque_abastecimento', form.errors)
        values['tanque_abastecimento'] = self.tanque.pk
        form = form_class(data=values)
        self.assertTrue(form.is_valid(), form.errors)
        created = form.save()
        self.assertEqual(created.tanque_abastecimento, self.tanque)
        self.assertFalse(created.is_staff)

    @override_settings(FORCE_SCRIPT_NAME='/homologacao', STATIC_URL='/homologacao/static/', AMBIENTE_HOMOLOGACAO=True)
    def test_prefixo_isola_rotas_login_e_manifest(self):
        # WSGI sets the script prefix for real proxy requests; ClientHandler does not.
        from django.urls import get_script_prefix, set_script_prefix
        previous = get_script_prefix()
        set_script_prefix('/homologacao/')
        try:
            html = self.client.get('/ceq/campo/', SCRIPT_NAME='/homologacao')
            self.assertEqual(html.status_code, 200)
            self.assertContains(html, 'HOMOLOGAÇÃO')
            self.assertContains(html, '/homologacao/ceq/campo/manifest.webmanifest')
            self.assertContains(html, '/homologacao/static/campo/campo.js')
            self.assertContains(html, '/homologacao/auth/login/')
            m = self.client.get('/ceq/campo/manifest.webmanifest', SCRIPT_NAME='/homologacao').json()
            self.assertEqual(m['scope'], '/homologacao/ceq/campo/')
            self.assertEqual(m['start_url'], '/homologacao/ceq/campo/')
            self.assertRedirects(self.client.get('/ceq/home/', SCRIPT_NAME='/homologacao'), '/homologacao/ceq/campo/', fetch_redirect_response=False)
            self.assertEqual(self.client.get('/ceq/campo/api/cadastros/', SCRIPT_NAME='/homologacao').status_code, 200)
        finally:
            set_script_prefix(previous)
