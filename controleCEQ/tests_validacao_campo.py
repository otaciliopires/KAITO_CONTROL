import json
from copy import deepcopy
from uuid import uuid4
from django.test import TestCase,Client
from django.utils import timezone
from autenticacao.models import Usuario
from ativos.models import Obras,Equipamentos
from .models import Tanque,Abastecimento,ValidacaoResponsavelCampo


class ValidacaoCampoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tanque=Tanque.objects.create(prefixo='VALIDA',tipo='M',capacidade=10000,estoque=0)
        cls.outro=Tanque.objects.create(prefixo='OUTRO',tipo='M',capacidade=10000,estoque=0)
        cls.user=Usuario.objects.create_user(username='validador',password='test',status='a',tanque_abastecimento=cls.tanque)
        cls.obra=Obras.objects.create(nome='Obra X')
        cls.y=Obras.objects.create(nome='Obra Y')
        cls.equip=Equipamentos.objects.create(prefixo='EQ-VALIDA')
        cls.signature={'versao':1,'tracos':[[[0.1,0.2],[0.3,0.4],[0.7,0.5]]]}

    def setUp(self): self.client.force_login(self.user)

    def lancar(self,obra=None,dia='2026-11-24'):
        p={'id':str(uuid4()),'usuario_id':self.user.pk,'tanque_id':self.tanque.pk,
            'obra_id':(obra or self.obra).pk,'equipamento_id':self.equip.pk,'data':dia,
            'contador_inicio':'0','contador_fim':'100','horimetro':'10','operador':'Motorista',
            'lubrificacao':False,'assinatura':self.signature,'registrado_em':timezone.now().isoformat()}
        response=self.client.post('/ceq/campo/api/enviar/',data=json.dumps(p),content_type='application/json')
        self.assertEqual(response.status_code,200)
        return p,Abastecimento.objects.get(pk=response.json()['abastecimento_id'])

    def batch(self,items,obra=None):
        return {'id':str(uuid4()),'usuario_id':self.user.pk,'obra_id':(obra or self.obra).pk,
            'data':'2026-11-24','responsavel':'Encarregado','assinatura':self.signature,
            'registrado_em':timezone.now().isoformat(),
            'registros':[{'id':p['id'],'conteudo':json.dumps(p,ensure_ascii=False)} for p,r in items]}

    def enviar(self,p): return self.client.post('/ceq/campo/api/validar-responsavel/',data=json.dumps(p),content_type='application/json')

    def test_cinco_x_sete_y_e_novos_x_nao_recebem_assinatura_anterior(self):
        x=[self.lancar() for _ in range(5)]
        y=[self.lancar(self.y) for _ in range(7)]
        group=self.batch(x)
        self.assertEqual(self.enviar(group).json()['quantidade'],5)
        after=[self.lancar() for _ in range(2)]
        self.assertEqual(Abastecimento.objects.filter(validacao_responsavel_id=group['id']).count(),5)
        self.assertFalse(Abastecimento.objects.filter(pk__in=[r.pk for p,r in y+after],validacao_responsavel__isnull=False).exists())
        second=self.batch(after)
        self.assertEqual(self.enviar(second).json()['quantidade'],2)
        self.assertEqual(Abastecimento.objects.filter(validacao_responsavel_id=group['id']).count(),5)
        self.assertEqual(ValidacaoResponsavelCampo.objects.count(),2)
        self.assertEqual(Abastecimento.objects.get(pk=x[0][1].pk).assinatura,self.signature)

    def test_validacao_opcional_e_reenvio_sem_duplicacao(self):
        row=self.lancar()
        self.assertIsNone(row[1].validacao_responsavel_id)
        group=self.batch([row]);a=self.enviar(group);b=self.enviar(group)
        self.assertEqual(a.status_code,200)
        self.assertEqual(a.json(),b.json())
        self.assertEqual(ValidacaoResponsavelCampo.objects.count(),1)
        group['responsavel']='Outro'
        self.assertEqual(self.enviar(group).status_code,409)

    def test_nao_substitui_validacao_existente(self):
        row=self.lancar();first=self.batch([row]);self.enviar(first)
        second=self.batch([row])
        self.assertEqual(self.enviar(second).status_code,409)
        row[1].refresh_from_db()
        self.assertEqual(str(row[1].validacao_responsavel_id),first['id'])
        self.assertEqual(ValidacaoResponsavelCampo.objects.count(),1)

    def test_nao_aceita_mistura_de_obras_dias_ou_payload_alterado(self):
        for rows in [[self.lancar(),self.lancar(self.y)],[self.lancar(),self.lancar(dia='2026-11-23')]]:
            self.assertEqual(self.enviar(self.batch(rows)).status_code,409)
        row=self.lancar();payload=self.batch([row]);changed=json.loads(payload['registros'][0]['conteudo']);changed['operador']='Mudou'
        payload['registros'][0]['conteudo']=json.dumps(changed)
        self.assertEqual(self.enviar(payload).status_code,409)
        self.assertEqual(ValidacaoResponsavelCampo.objects.count(),0)
        self.assertFalse(Abastecimento.objects.filter(validacao_responsavel__isnull=False).exists())

    def test_aguarda_todos_os_abastecimentos_sem_criar_vinculo_parcial(self):
        row=self.lancar();p=deepcopy(row[0]);p['id']=str(uuid4())
        batch=self.batch([row,(p,None)])
        self.assertEqual(self.enviar(batch).status_code,425)
        self.assertFalse(ValidacaoResponsavelCampo.objects.exists())
        row[1].refresh_from_db();self.assertIsNone(row[1].validacao_responsavel_id)

    def test_escopo_usuario_e_tanque(self):
        row=self.lancar();payload=self.batch([row])
        other=Usuario.objects.create_user(username='outro_validador',status='a',tanque_abastecimento=self.tanque)
        self.client.force_login(other)
        self.assertEqual(self.enviar(payload).status_code,403)
        payload['usuario_id']=other.pk
        self.assertEqual(self.enviar(payload).status_code,403)
        self.client.force_login(self.user)
        self.user.tanque_abastecimento=self.outro;self.user.save()
        payload['usuario_id']=self.user.pk
        self.assertEqual(self.enviar(payload).status_code,403)
        self.assertFalse(ValidacaoResponsavelCampo.objects.exists())

    def test_assinatura_obrigatoria_para_validar_e_lote_nao_vazio(self):
        row=self.lancar()
        for field,value in [('assinatura',{}),('assinatura',{'versao':1,'tracos':[[[0,0],[2,1]]]}),('registros',[]),('registros',[{'id':row[0]['id'],'conteudo':'{}'}]),('data','invalida')]:
            batch=self.batch([row]);batch[field]=value
            self.assertEqual(self.enviar(batch).status_code,400)
        batch=self.batch([row]);batch['registros']*=2
        self.assertEqual(self.enviar(batch).status_code,400)
        self.assertFalse(ValidacaoResponsavelCampo.objects.exists())

    def test_login_csrf_e_metodo(self):
        row=self.lancar();batch=self.batch([row])
        self.assertEqual(self.client.get('/ceq/campo/api/validar-responsavel/').status_code,405)
        strict=Client(enforce_csrf_checks=True);strict.force_login(self.user)
        self.assertEqual(strict.post('/ceq/campo/api/validar-responsavel/',data=json.dumps(batch),content_type='application/json').status_code,403)
        self.client.logout();self.assertEqual(self.enviar(batch).status_code,401)

    def test_tela_e_cache_contem_validacao_sem_mudar_assinatura_motorista(self):
        page=self.client.get('/ceq/campo/')
        self.assertContains(page,'Validação responsável')
        self.assertContains(page,'id="validacao-dialog"')
        self.assertContains(page,'id="assinatura-responsavel"')
        self.assertContains(page,'id="assinatura"')
        worker=self.client.get('/ceq/campo/sw.js').content.decode()
        self.assertIn('validacao_responsavel.js',worker)
        self.assertIn("PREFIX+'v10'",worker)
