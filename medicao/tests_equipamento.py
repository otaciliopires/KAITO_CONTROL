"""
Testes da medição de equipamentos. Arquivo próprio, separado de tests.py
(que cobre o fluxo de caminhão) por convenção do módulo.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from ativos.models import Equipamentos, Obras
from controleCEQ.models import Tanque
from medicao import calculos_equipamento as calc
from medicao import servicos_equipamento as servicos
from medicao.models import CaminhaoAbastecedor
from medicao.models_equipamento import (
    MedicaoEquipamento,
    MotivoParada,
    PeriodoMedicaoEquipamento,
    ValorMensalEquipamento,
    VinculoCaminhaoEquipamento,
)

Usuario = get_user_model()


class FracaoHorimetroTests(SimpleTestCase):
    """Os 5 casos obrigatórios da tabela do processo atual, com JORNADA_UTIL=9h."""

    def test_dia_normal_sem_parada(self):
        fracao = calc.calcular_fracao_horimetro(
            parada_horas=Decimal('0'), horas_trabalhadas=Decimal('8.7'), jornada_util=Decimal('9')
        )
        self.assertEqual(fracao, Decimal('1.00'))

    def test_fim_de_semana_sem_apontamento(self):
        fracao = calc.calcular_fracao_horimetro(
            parada_horas=Decimal('0'), horas_trabalhadas=Decimal('0'), jornada_util=Decimal('9')
        )
        self.assertEqual(fracao, Decimal('1.00'))

    def test_parada_falta_de_diesel(self):
        fracao = calc.calcular_fracao_horimetro(
            parada_horas=Decimal('1.67'), horas_trabalhadas=Decimal('7.3'), jornada_util=Decimal('9')
        )
        self.assertEqual(fracao, Decimal('0.81'))

    def test_manutencao_mas_trabalhou_fora_do_expediente(self):
        fracao = calc.calcular_fracao_horimetro(
            parada_horas=Decimal('5.0'), horas_trabalhadas=Decimal('5.0'), jornada_util=Decimal('9')
        )
        self.assertEqual(fracao, Decimal('0.56'))

    def test_manutencao_dia_inteiro(self):
        fracao = calc.calcular_fracao_horimetro(
            parada_horas=Decimal('9.0'), horas_trabalhadas=Decimal('0'), jornada_util=Decimal('9')
        )
        self.assertEqual(fracao, Decimal('0.00'))

    def test_fracao_nunca_negativa_nem_maior_que_um(self):
        # parada exagerada não pode gerar base negativa sem clamp
        fracao = calc.calcular_fracao_horimetro(
            parada_horas=Decimal('20'), horas_trabalhadas=Decimal('0'), jornada_util=Decimal('9')
        )
        self.assertEqual(fracao, Decimal('0.00'))

    @override_settings(JORNADA_UTIL_HORAS=9)
    def test_usa_settings_quando_jornada_nao_informada(self):
        fracao = calc.calcular_fracao_horimetro(parada_horas=Decimal('0'), horas_trabalhadas=Decimal('0'))
        self.assertEqual(fracao, Decimal('1.00'))
        self.assertEqual(calc.jornada_util_horas(), Decimal('9'))


class FracaoOdometroTests(SimpleTestCase):
    def test_sem_parada_fracao_um(self):
        fracao = calc.calcular_fracao_odometro(parada_horas=Decimal('0'), jornada_util=Decimal('9'))
        self.assertEqual(fracao, Decimal('1.00'))

    def test_com_parada_proporcional(self):
        # 1.67h de parada numa jornada de 9h -> 1 - 1.67/9 = 0.8144... -> 0.81
        fracao = calc.calcular_fracao_odometro(parada_horas=Decimal('1.67'), jornada_util=Decimal('9'))
        self.assertEqual(fracao, Decimal('0.81'))

    def test_parada_dia_inteiro(self):
        fracao = calc.calcular_fracao_odometro(parada_horas=Decimal('9'), jornada_util=Decimal('9'))
        self.assertEqual(fracao, Decimal('0.00'))


class DestinoComplementoTests(SimpleTestCase):
    def test_sem_complemento_nao_exige_motivo(self):
        resultado = calc.classificar_complemento(Decimal('1.00'), destino_complemento=None)
        self.assertEqual(resultado, calc.ComplementoDia(Decimal('0.00'), Decimal('0.00')))

    def test_complemento_vai_para_manutencao(self):
        resultado = calc.classificar_complemento(Decimal('0.56'), destino_complemento=calc.DESTINO_MANUTENCAO)
        self.assertEqual(resultado.dias_manutencao, Decimal('0.44'))
        self.assertEqual(resultado.dias_disposicao, Decimal('0.00'))

    def test_complemento_vai_para_disposicao(self):
        resultado = calc.classificar_complemento(Decimal('0.81'), destino_complemento=calc.DESTINO_DISPOSICAO)
        self.assertEqual(resultado.dias_disposicao, Decimal('0.19'))
        self.assertEqual(resultado.dias_manutencao, Decimal('0.00'))

    def test_dia_inteiro_perdido_cai_todo_no_motivo(self):
        resultado = calc.classificar_complemento(Decimal('0.00'), destino_complemento=calc.DESTINO_MANUTENCAO)
        self.assertEqual(resultado.dias_manutencao, Decimal('1.00'))

    def test_complemento_sem_motivo_e_erro(self):
        with self.assertRaises(ValueError):
            calc.classificar_complemento(Decimal('0.56'), destino_complemento=None)

    def test_destino_desconhecido_e_erro(self):
        with self.assertRaises(ValueError):
            calc.classificar_complemento(Decimal('0.56'), destino_complemento='ALGO_INVALIDO')


class DerivarTipoDiaTests(SimpleTestCase):
    def test_fracao_um_e_trabalho(self):
        self.assertEqual(calc.derivar_tipo_dia(Decimal('1.00'), None), calc.TIPO_TRABALHO)

    def test_fracao_parcial_e_trabalho(self):
        self.assertEqual(calc.derivar_tipo_dia(Decimal('0.56'), calc.DESTINO_MANUTENCAO), calc.TIPO_TRABALHO)

    def test_fracao_zero_manutencao(self):
        self.assertEqual(calc.derivar_tipo_dia(Decimal('0.00'), calc.DESTINO_MANUTENCAO), calc.TIPO_MANUTENCAO)

    def test_fracao_zero_disposicao(self):
        self.assertEqual(calc.derivar_tipo_dia(Decimal('0.00'), calc.DESTINO_DISPOSICAO), calc.TIPO_DISPOSICAO)

    def test_fracao_zero_sem_motivo_e_erro(self):
        with self.assertRaises(ValueError):
            calc.derivar_tipo_dia(Decimal('0.00'), None)


class RateioFinanceiroTests(SimpleTestCase):
    def test_exemplo_do_enunciado_dois_meses_15_15(self):
        # R$10.000/mês, 15 dias na obra A e 15 na B, mês de 30 dias -> R$5.000 cada
        valor_a = calc.calcular_valor_rateio(Decimal('15'), 30, Decimal('10000'))
        valor_b = calc.calcular_valor_rateio(Decimal('15'), 30, Decimal('10000'))
        self.assertEqual(valor_a, Decimal('5000.00'))
        self.assertEqual(valor_b, Decimal('5000.00'))

    def test_fator_rateio(self):
        fator = calc.calcular_fator_rateio(Decimal('10'), 30)
        self.assertEqual(fator, Decimal('10') / Decimal('30'))

    def test_dias_do_mes_invalido(self):
        with self.assertRaises(ValueError):
            calc.calcular_fator_rateio(Decimal('10'), 0)

    def test_rateio_manutencao_mesma_formula(self):
        valor = calc.calcular_valor_rateio(Decimal('3'), 30, Decimal('27000'))
        self.assertEqual(valor, Decimal('2700.00'))


class ConsolidacaoEFechamentoTests(SimpleTestCase):
    def test_soma_correta_fecha_sem_divergencia(self):
        apontamentos = [
            calc.ApontamentoParaConsolidar(obra_id=1, dias_obra=Decimal('15.00'), dias_manutencao=Decimal('0.00'), dias_disposicao=Decimal('0.00')),
            calc.ApontamentoParaConsolidar(obra_id=2, dias_obra=Decimal('12.00'), dias_manutencao=Decimal('0.00'), dias_disposicao=Decimal('0.00')),
            calc.ApontamentoParaConsolidar(obra_id=2, dias_obra=Decimal('0.00'), dias_manutencao=Decimal('2.00'), dias_disposicao=Decimal('0.00')),
            calc.ApontamentoParaConsolidar(obra_id=2, dias_obra=Decimal('0.00'), dias_manutencao=Decimal('0.00'), dias_disposicao=Decimal('1.00')),
        ]
        consolidado = calc.consolidar_mes(apontamentos)
        self.assertEqual(consolidado.dias_por_obra, {1: Decimal('15.00'), 2: Decimal('12.00')})
        self.assertEqual(consolidado.dias_manutencao, Decimal('2.00'))
        self.assertEqual(consolidado.dias_disposicao, Decimal('1.00'))
        self.assertEqual(consolidado.total_dias, Decimal('30.00'))

        divergencia = calc.calcular_divergencia_fechamento(consolidado, dias_do_mes=30)
        self.assertEqual(divergencia, Decimal('0.00'))

    def test_soma_incorreta_gera_divergencia(self):
        apontamentos = [
            calc.ApontamentoParaConsolidar(obra_id=1, dias_obra=Decimal('20.00'), dias_manutencao=Decimal('0.00'), dias_disposicao=Decimal('0.00')),
            calc.ApontamentoParaConsolidar(obra_id=1, dias_obra=Decimal('0.00'), dias_manutencao=Decimal('5.00'), dias_disposicao=Decimal('0.00')),
        ]
        consolidado = calc.consolidar_mes(apontamentos)
        self.assertEqual(consolidado.total_dias, Decimal('25.00'))

        divergencia = calc.calcular_divergencia_fechamento(consolidado, dias_do_mes=30)
        self.assertEqual(divergencia, Decimal('-5.00'))
        self.assertNotEqual(divergencia, Decimal('0.00'))


class AbrirMedicaoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-12', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('27000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 2)

    def test_abre_medicao_e_pre_cria_um_dia_por_data_do_periodo(self):
        medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)
        self.assertEqual(medicao.status, MedicaoEquipamento.STATUS_RASCUNHO)
        self.assertEqual(medicao.apontamentos.count(), self.periodo.dias_do_mes)
        self.assertEqual(medicao.valor_aluguel_vigente, Decimal('27000.00'))
        primeiro_dia = medicao.apontamentos.order_by('data').first()
        self.assertFalse(primeiro_dia.preenchido)

    def test_nao_permite_equipamento_nao_elegivel(self):
        self.equipamento.elegivel_medicao = False
        self.equipamento.save()
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)

    def test_nao_permite_duas_medicoes_da_mesma_obra_no_periodo(self):
        servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)

    def test_permite_medicoes_de_obras_diferentes_no_mesmo_periodo(self):
        medicao1 = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)
        outra_obra = Obras.objects.create(nome='Obra 2')
        medicao2 = servicos.abrir_medicao(self.periodo, self.equipamento, outra_obra, self.usuario)
        self.assertNotEqual(medicao1.id, medicao2.id)
        self.assertEqual(medicao1.obra, self.obra)
        self.assertEqual(medicao2.obra, outra_obra)

    def test_obra_ja_medida_some_da_lista_mas_outra_obra_continua_vendo(self):
        servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)
        outra_obra = Obras.objects.create(nome='Obra 2')
        self.assertNotIn(
            self.equipamento, list(servicos.equipamentos_disponiveis_para_medicao(self.periodo, self.obra))
        )
        self.assertIn(
            self.equipamento, list(servicos.equipamentos_disponiveis_para_medicao(self.periodo, outra_obra))
        )

    def test_exclui_equipamento_vinculado_a_caminhao_abastecedor(self):
        tanque = Tanque.objects.create(prefixo='TQ-01', capacidade=1000, estoque=0, tipo='M')
        caminhao = CaminhaoAbastecedor.objects.create(tanque=tanque, identificacao='CAM-01')
        VinculoCaminhaoEquipamento.objects.create(equipamento=self.equipamento, caminhao_abastecedor=caminhao)

        disponiveis = list(servicos.equipamentos_disponiveis_para_medicao(self.periodo))
        self.assertNotIn(self.equipamento, disponiveis)
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)

    def test_sem_valor_de_aluguel_cadastrado_bloqueia(self):
        equipamento_sem_valor = Equipamentos.objects.create(
            prefixo='CB-05', elegivel_medicao=True, unidade_medicao='H'
        )
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao(self.periodo, equipamento_sem_valor, self.obra, self.usuario)


class ObraResponsavelPelaCobrancaTests(TestCase):
    """`obra_do_dia` é só uma anotação da obra sobre onde a máquina rodou —
    nunca decide quem é cobrado. A cobrança de todo dia de trabalho é sempre
    da obra dona da medição (quem a abriu), mesmo que a obra informe uma
    obra_do_dia diferente da sua."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Walter Brito')
        self.obra.usuario.add(self.usuario)
        self.outra_obra = Obras.objects.create(nome='Canal')
        self.equipamento = Equipamentos.objects.create(prefixo='EH-70', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 10)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)

    def test_dia_informado_para_outra_obra_ainda_conta_para_a_obra_da_medicao(self):
        ap = self.medicao.apontamentos.first()
        servicos.salvar_dia(
            ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
            parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.outra_obra,
        )
        ap.refresh_from_db()
        self.assertEqual(ap.obra_do_dia_id, self.outra_obra.id)  # a anotação foi salva

        consolidado = servicos.consolidar_medicao(self.medicao)
        self.assertEqual(consolidado.dias_por_obra, {self.obra.id: Decimal('1.00')})
        self.assertNotIn(self.outra_obra.id, consolidado.dias_por_obra)

    def test_obras_diferentes_podem_apontar_o_mesmo_dia_da_mesma_maquina(self):
        medicao_outra_obra = servicos.abrir_medicao(self.periodo, self.equipamento, self.outra_obra, self.usuario)
        data_comum = self.medicao.apontamentos.first().data

        ap1 = self.medicao.apontamentos.get(data=data_comum)
        ap2 = medicao_outra_obra.apontamentos.get(data=data_comum)

        servicos.salvar_dia(
            ap1, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
            parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
        )
        servicos.salvar_dia(
            ap2, contador_inicial=Decimal('0'), contador_final=Decimal('5'),
            parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.outra_obra,
        )

        self.assertEqual(
            servicos.consolidar_medicao(self.medicao).dias_por_obra, {self.obra.id: Decimal('1.00')}
        )
        self.assertEqual(
            servicos.consolidar_medicao(medicao_outra_obra).dias_por_obra, {self.outra_obra.id: Decimal('1.00')}
        )


class SalvarDiaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-12', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 3)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)
        self.motivo_manutencao = MotivoParada.objects.create(
            descricao='Manutenção corretiva', destino_complemento=calc.DESTINO_MANUTENCAO
        )

    def test_dia_normal_sem_parada(self):
        ap = self.medicao.apontamentos.first()
        ap, avisos = servicos.salvar_dia(
            ap, contador_inicial=Decimal('100'), contador_final=Decimal('108.7'),
            parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
        )
        self.assertEqual(ap.fracao_calculada, Decimal('1.00'))
        self.assertEqual(ap.tipo_dia, calc.TIPO_TRABALHO)
        self.assertEqual(avisos, [])

    def test_contador_final_menor_que_inicial_bloqueia_e_nao_salva(self):
        ap = self.medicao.apontamentos.first()
        with self.assertRaises(servicos.ValidacaoDia):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('100'), contador_final=Decimal('90'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )
        ap.refresh_from_db()
        self.assertFalse(ap.preenchido)

    def test_parada_maior_que_jornada_bloqueia(self):
        ap = self.medicao.apontamentos.first()
        with self.assertRaises(servicos.ValidacaoDia):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('100'), contador_final=Decimal('100'),
                parada_horas=Decimal('10'), motivo=self.motivo_manutencao, obra_do_dia=self.obra,
            )

    def test_parada_sem_motivo_bloqueia(self):
        ap = self.medicao.apontamentos.first()
        with self.assertRaises(servicos.ValidacaoDia):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('100'), contador_final=Decimal('100'),
                parada_horas=Decimal('5'), motivo=None, obra_do_dia=self.obra,
            )

    def test_dia_de_manutencao_o_dia_inteiro(self):
        ap = self.medicao.apontamentos.first()
        ap, avisos = servicos.salvar_dia(
            ap, contador_inicial=Decimal('100'), contador_final=Decimal('100'),
            parada_horas=Decimal('9'), motivo=self.motivo_manutencao, obra_do_dia=self.obra,
        )
        self.assertEqual(ap.fracao_calculada, Decimal('0.00'))
        self.assertEqual(ap.tipo_dia, calc.TIPO_MANUTENCAO)

    def test_medicao_fora_de_rascunho_bloqueia_edicao(self):
        servicos.enviar_para_central(self.medicao, self.usuario)
        ap = self.medicao.apontamentos.first()
        with self.assertRaises(servicos.ValidacaoDia):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )


class TransicoesStatusTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-12', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('10000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 4)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)

    def test_enviar_de_rascunho_muda_status(self):
        servicos.enviar_para_central(self.medicao, self.usuario)
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_ENVIADA)
        self.assertIsNotNone(self.medicao.enviada_em)

    def test_enviar_fora_de_rascunho_bloqueia(self):
        servicos.enviar_para_central(self.medicao, self.usuario)
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.enviar_para_central(self.medicao, self.usuario)

    def test_confirmar_exige_devolvida(self):
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.confirmar_e_fechar(self.medicao, self.usuario)

    def test_confirmar_bloqueia_com_divergencia(self):
        self.medicao.status = MedicaoEquipamento.STATUS_DEVOLVIDA
        self.medicao.save()
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.confirmar_e_fechar(self.medicao, self.usuario)

    def test_confirmar_fecha_quando_devolvida_e_mes_fecha_certo(self):
        for ap in self.medicao.apontamentos.order_by('data'):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )
        self.medicao.refresh_from_db()
        self.medicao.status = MedicaoEquipamento.STATUS_DEVOLVIDA
        self.medicao.save()
        servicos.confirmar_e_fechar(self.medicao, self.usuario)
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_FECHADA)

    def test_contestar_exige_devolvida(self):
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.contestar(self.medicao, self.usuario, 'discordo')

    def test_contestar_exige_justificativa(self):
        self.medicao.status = MedicaoEquipamento.STATUS_DEVOLVIDA
        self.medicao.save()
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.contestar(self.medicao, self.usuario, '   ')

    def test_contestar_volta_para_em_analise(self):
        self.medicao.status = MedicaoEquipamento.STATUS_DEVOLVIDA
        self.medicao.save()
        servicos.contestar(self.medicao, self.usuario, 'discordo do ajuste')
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_EM_ANALISE)


class CeqTransicoesTests(TestCase):
    def setUp(self):
        self.usuario_obra = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.usuario_ceq = Usuario.objects.create_user(username='ceq1', password='x', status='c')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario_obra)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-20', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 6)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario_obra)

    def _preencher_mes_completo(self):
        for ap in self.medicao.apontamentos.order_by('data'):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )

    def test_iniciar_analise_exige_enviada(self):
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.iniciar_analise(self.medicao, self.usuario_ceq)

    def test_iniciar_analise_muda_status(self):
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_EM_ANALISE)

    def test_aprovar_sem_ajuste_bloqueia_com_divergencia(self):
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.aprovar_sem_ajuste(self.medicao, self.usuario_ceq)

    def test_aprovar_sem_ajuste_fecha_quando_bate(self):
        self._preencher_mes_completo()
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        servicos.aprovar_sem_ajuste(self.medicao, self.usuario_ceq)
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_FECHADA)

    def test_ajustar_e_devolver_exige_pelo_menos_um_ajuste(self):
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.ajustar_e_devolver(self.medicao, self.usuario_ceq, [])

    def test_ajustar_e_devolver_exige_justificativa(self):
        self._preencher_mes_completo()
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.ajustar_e_devolver(self.medicao, self.usuario_ceq, [
                {'obra': self.obra, 'dias_apontados_obra': Decimal('30'), 'dias_aplicados_admin': Decimal('28'), 'justificativa': ''},
            ])

    def test_ajustar_e_devolver_cria_ajuste_e_devolve(self):
        self._preencher_mes_completo()
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        servicos.ajustar_e_devolver(self.medicao, self.usuario_ceq, [
            {
                'obra': self.obra, 'dias_apontados_obra': Decimal('30'),
                'dias_aplicados_admin': Decimal('28'), 'justificativa': 'dois dias sem apontamento válido',
            },
        ])
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_DEVOLVIDA)
        self.assertEqual(self.medicao.ajustes_admin.count(), 1)

    def test_reabrir_medicao_exige_fechada(self):
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.reabrir_medicao(self.medicao, self.usuario_ceq, 'justificativa')

    def test_reabrir_medicao_exige_justificativa(self):
        self._preencher_mes_completo()
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        servicos.aprovar_sem_ajuste(self.medicao, self.usuario_ceq)
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.reabrir_medicao(self.medicao, self.usuario_ceq, '')

    def test_reabrir_medicao_volta_para_em_analise(self):
        self._preencher_mes_completo()
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        servicos.aprovar_sem_ajuste(self.medicao, self.usuario_ceq)
        servicos.reabrir_medicao(self.medicao, self.usuario_ceq, 'erro de digitação')
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_EM_ANALISE)

    def test_lancar_manutencao_admin_valida_dias_e_justificativa(self):
        with self.assertRaises(servicos.ValidacaoLancamento):
            servicos.lancar_manutencao_admin(self.medicao, self.usuario_ceq, '0', 'motivo')
        with self.assertRaises(servicos.ValidacaoLancamento):
            servicos.lancar_manutencao_admin(self.medicao, self.usuario_ceq, '2', '')
        lancamento = servicos.lancar_manutencao_admin(self.medicao, self.usuario_ceq, '2', 'ok')
        self.assertEqual(lancamento.origem, 'ADMIN')

    def test_fechar_periodo_bloqueia_com_medicao_pendente(self):
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.fechar_periodo(self.periodo)

    def test_fechar_e_reabrir_periodo(self):
        self._preencher_mes_completo()
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        servicos.aprovar_sem_ajuste(self.medicao, self.usuario_ceq)

        servicos.fechar_periodo(self.periodo)
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.status, 'FECHADO')

        servicos.reabrir_periodo(self.periodo)
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.status, 'ABERTO')


class PermissaoCeqViewsTests(TestCase):
    def setUp(self):
        self.usuario_obra = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.usuario_ceq = Usuario.objects.create_user(username='ceq1', password='x', status='c')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario_obra)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-30', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 7)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario_obra)

    def test_ceq_acessa_painel(self):
        self.client.force_login(self.usuario_ceq)
        resp = self.client.get('/medicao/equip/ceq/')
        self.assertEqual(resp.status_code, 200)

    def test_obra_nao_acessa_painel_ceq(self):
        self.client.force_login(self.usuario_obra)
        resp = self.client.get('/medicao/equip/ceq/')
        self.assertContains(resp, 'Acesso negado')

    def test_obra_nao_pode_aprovar_medicao(self):
        self.client.force_login(self.usuario_obra)
        resp = self.client.post(f'/medicao/equip/ceq/medicao/{self.medicao.id}/aprovar/')
        self.assertContains(resp, 'Acesso negado')
        self.medicao.refresh_from_db()
        self.assertEqual(self.medicao.status, MedicaoEquipamento.STATUS_RASCUNHO)

    def test_obra_nao_pode_fechar_periodo(self):
        self.client.force_login(self.usuario_obra)
        resp = self.client.post(f'/medicao/equip/ceq/periodo/{self.periodo.id}/fechar/')
        self.assertContains(resp, 'Acesso negado')
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.status, PeriodoMedicaoEquipamento.STATUS_ABERTO)

    def test_ceq_nao_pode_editar_dia_da_grade_obra(self):
        # a view de CEQ não expõe edição de apontamento algum; o service continua
        # bloqueando fora de RASCUNHO independentemente de quem chama.
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        ap = self.medicao.apontamentos.first()
        with self.assertRaises(servicos.ValidacaoDia):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )


class PeriodoFechadoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-31', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 8)
        self.periodo.status = PeriodoMedicaoEquipamento.STATUS_FECHADO
        self.periodo.save()

    def test_nao_abre_medicao_em_periodo_fechado(self):
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario)


class CicloDeVidaCompletoTests(TestCase):
    """Percorre toda a máquina de estados do enunciado, checando o histórico
    a cada transição: RASCUNHO -> ENVIADA -> EM_ANALISE -> DEVOLVIDA
    -> (contesta) -> EM_ANALISE -> (ajusta) -> DEVOLVIDA -> (obra confirma)
    -> FECHADA -> (admin reabre) -> EM_ANALISE -> (aprova sem ajuste) -> FECHADA."""

    def setUp(self):
        self.usuario_obra = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.usuario_ceq = Usuario.objects.create_user(username='ceq1', password='x', status='c')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario_obra)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-40', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 9)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario_obra)
        for ap in self.medicao.apontamentos.order_by('data'):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )

    def test_ciclo_completo(self):
        m = self.medicao

        servicos.enviar_para_central(m, self.usuario_obra)
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_ENVIADA)

        servicos.iniciar_analise(m, self.usuario_ceq)
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_EM_ANALISE)

        servicos.ajustar_e_devolver(m, self.usuario_ceq, [{
            'obra': self.obra, 'dias_apontados_obra': Decimal('30'),
            'dias_aplicados_admin': Decimal('28'), 'justificativa': 'ajuste 1',
        }])
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_DEVOLVIDA)

        servicos.contestar(m, self.usuario_obra, 'não concordo, tenho os apontamentos')
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_EM_ANALISE)

        servicos.ajustar_e_devolver(m, self.usuario_ceq, [{
            'obra': self.obra, 'dias_apontados_obra': Decimal('30'),
            'dias_aplicados_admin': Decimal('30'), 'justificativa': 'revertido após contestação',
        }])
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_DEVOLVIDA)

        servicos.confirmar_e_fechar(m, self.usuario_obra)
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_FECHADA)

        servicos.reabrir_medicao(m, self.usuario_ceq, 'precisa corrigir um lançamento de manutenção')
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_EM_ANALISE)

        servicos.aprovar_sem_ajuste(m, self.usuario_ceq)
        m.refresh_from_db()
        self.assertEqual(m.status, MedicaoEquipamento.STATUS_FECHADA)

        # 8 transições de status ao todo -> 8 entradas de histórico com campo 'status'
        historico_status = m.historico.filter(campo='status').order_by('data_hora')
        self.assertEqual(historico_status.count(), 8)
        for entrada in historico_status:
            self.assertIsNotNone(entrada.usuario)
            self.assertIsNotNone(entrada.data_hora)

        # os dois ajustes ficam registrados lado a lado, nenhum sobrescreve o outro
        self.assertEqual(m.ajustes_admin.count(), 2)

        # tentar editar apontamento fora de RASCUNHO continua bloqueado no fim do ciclo
        with self.assertRaises(servicos.ValidacaoDia):
            servicos.salvar_dia(
                m.apontamentos.first(), contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )


class PdfBoletimTests(TestCase):
    def setUp(self):
        self.usuario_obra = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.usuario_ceq = Usuario.objects.create_user(username='ceq1', password='x', status='c')
        self.outro_obra = Usuario.objects.create_user(username='obra2', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario_obra)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-50', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 11)
        self.medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario_obra)

    def test_boletim_bloqueia_antes_de_fechar(self):
        self.client.force_login(self.usuario_ceq)
        resp = self.client.get(f'/medicao/equip/medicao/{self.medicao.id}/boletim.pdf', follow=True)
        self.assertContains(resp, 'Feche a medição antes de baixar o boletim.')

    def test_boletim_nega_obra_sem_vinculo(self):
        self.client.force_login(self.outro_obra)
        resp = self.client.get(f'/medicao/equip/medicao/{self.medicao.id}/boletim.pdf')
        self.assertContains(resp, 'Acesso negado')

    def test_boletim_gerado_apos_fechar(self):
        for ap in self.medicao.apontamentos.order_by('data'):
            servicos.salvar_dia(
                ap, contador_inicial=Decimal('0'), contador_final=Decimal('8'),
                parada_horas=Decimal('0'), motivo=None, obra_do_dia=self.obra,
            )
        servicos.enviar_para_central(self.medicao, self.usuario_obra)
        servicos.iniciar_analise(self.medicao, self.usuario_ceq)
        servicos.aprovar_sem_ajuste(self.medicao, self.usuario_ceq)

        self.client.force_login(self.usuario_obra)
        resp = self.client.get(f'/medicao/equip/medicao/{self.medicao.id}/boletim.pdf')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_resumo_periodo_nega_obra(self):
        self.client.force_login(self.usuario_obra)
        resp = self.client.get(f'/medicao/equip/ceq/periodo/{self.periodo.id}/resumo.pdf')
        self.assertContains(resp, 'Acesso negado')

    def test_resumo_periodo_ceq(self):
        self.client.force_login(self.usuario_ceq)
        resp = self.client.get(f'/medicao/equip/ceq/periodo/{self.periodo.id}/resumo.pdf')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')


class MedicaoSemObraTests(TestCase):
    """Equipamento parado em manutenção/à disposição sem nenhuma obra
    envolvida — máquina que fica meses na oficina, perdendo relação com a
    obra que a estava usando."""

    def setUp(self):
        self.usuario_ceq = Usuario.objects.create_user(username='ceq1', password='x', status='c')
        self.usuario_obra = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario_obra)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-60', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2026, 12)

    def test_abrir_medicao_ceq_nao_cria_apontamento_diario(self):
        medicao = servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)
        self.assertIsNone(medicao.obra_id)
        self.assertEqual(medicao.status, MedicaoEquipamento.STATUS_RASCUNHO)
        self.assertEqual(medicao.apontamentos.count(), 0)

    def test_abrir_medicao_ceq_reusa_mesmas_validacoes(self):
        self.equipamento.elegivel_medicao = False
        self.equipamento.save()
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)

    def test_abrir_medicao_ceq_impede_duplicidade_com_medicao_de_obra(self):
        servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario_obra)
        with self.assertRaises(servicos.AberturaInvalida):
            servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)

    def test_fechar_medicao_ceq_bloqueia_com_divergencia(self):
        medicao = servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)
        servicos.lancar_manutencao_admin(medicao, self.usuario_ceq, '10', 'só uma parte do mês')
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.fechar_medicao_ceq(medicao, self.usuario_ceq)

    def test_fechar_medicao_ceq_fecha_quando_bate(self):
        medicao = servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)
        servicos.lancar_manutencao_admin(medicao, self.usuario_ceq, '20', 'reforma do motor')
        servicos.lancar_disposicao_admin(medicao, self.usuario_ceq, str(self.periodo.dias_do_mes - 20), 'aguardando obra nova')
        servicos.fechar_medicao_ceq(medicao, self.usuario_ceq)
        medicao.refresh_from_db()
        self.assertEqual(medicao.status, MedicaoEquipamento.STATUS_FECHADA)

    def test_fechar_medicao_ceq_recusa_medicao_com_obra(self):
        medicao = servicos.abrir_medicao(self.periodo, self.equipamento, self.obra, self.usuario_obra)
        with self.assertRaises(servicos.TransicaoInvalida):
            servicos.fechar_medicao_ceq(medicao, self.usuario_ceq)

    def test_reabrir_medicao_sem_obra_volta_para_rascunho(self):
        medicao = servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)
        servicos.lancar_manutencao_admin(medicao, self.usuario_ceq, str(self.periodo.dias_do_mes), 'mês inteiro na oficina')
        servicos.fechar_medicao_ceq(medicao, self.usuario_ceq)
        servicos.reabrir_medicao(medicao, self.usuario_ceq, 'preciso corrigir os dias')
        medicao.refresh_from_db()
        self.assertEqual(medicao.status, MedicaoEquipamento.STATUS_RASCUNHO)

    def test_matriz_localizacao_inclui_medicao_sem_obra(self):
        medicao = servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)
        servicos.lancar_manutencao_admin(medicao, self.usuario_ceq, '15', 'motor')
        obras_colunas, linhas = servicos.matriz_localizacao(self.periodo)
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]['manutencao'], Decimal('15'))
        self.assertEqual(linhas[0]['dias_por_coluna'], [])  # nenhuma obra nas colunas ainda


class PermissaoMedicaoSemObraViewsTests(TestCase):
    def setUp(self):
        self.usuario_ceq = Usuario.objects.create_user(username='ceq1', password='x', status='c')
        self.usuario_obra = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario_obra)
        self.equipamento = Equipamentos.objects.create(prefixo='EH-61', elegivel_medicao=True, unidade_medicao='H')
        ValorMensalEquipamento.objects.create(
            equipamento=self.equipamento, valor=Decimal('9000'), vigente_desde=date(2020, 1, 1)
        )
        self.periodo = servicos.obter_ou_criar_periodo(2027, 1)

    def test_obra_nao_abre_medicao_direta(self):
        self.client.force_login(self.usuario_obra)
        resp = self.client.post(f'/medicao/equip/ceq/periodo/{self.periodo.id}/nova-direta/', {
            'equipamento': self.equipamento.id,
        })
        self.assertContains(resp, 'Acesso negado')
        self.assertFalse(MedicaoEquipamento.objects.filter(periodo=self.periodo, equipamento=self.equipamento).exists())

    def test_ceq_abre_medicao_direta_pela_view(self):
        self.client.force_login(self.usuario_ceq)
        resp = self.client.post(f'/medicao/equip/ceq/periodo/{self.periodo.id}/nova-direta/', {
            'equipamento': self.equipamento.id,
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        medicao = MedicaoEquipamento.objects.get(periodo=self.periodo, equipamento=self.equipamento)
        self.assertIsNone(medicao.obra_id)

    def test_obra_usuario_nao_acessa_medicao_sem_obra_pelo_lado_obra(self):
        medicao = servicos.abrir_medicao_ceq(self.periodo, self.equipamento, self.usuario_ceq)
        self.client.force_login(self.usuario_obra)
        resp = self.client.get(f'/medicao/equip/medicao/{medicao.id}/')
        self.assertContains(resp, 'Acesso negado')

    def test_localizacao_renderiza_para_ceq(self):
        self.client.force_login(self.usuario_ceq)
        resp = self.client.get('/medicao/equip/ceq/localizacao/')
        self.assertEqual(resp.status_code, 200)

    def test_localizacao_nega_obra(self):
        self.client.force_login(self.usuario_obra)
        resp = self.client.get('/medicao/equip/ceq/localizacao/')
        self.assertContains(resp, 'Acesso negado')


class PermissaoViewsTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='obra1', password='x', status='o')
        self.obra = Obras.objects.create(nome='Obra 1')
        self.obra.usuario.add(self.usuario)
        self.outra_obra = Obras.objects.create(nome='Obra 2')
        self.client.force_login(self.usuario)

    def test_obra_acessa_periodos_da_propria_obra(self):
        resp = self.client.get(f'/medicao/equip/{self.obra.id}/periodos/')
        self.assertEqual(resp.status_code, 200)

    def test_obra_nao_acessa_periodos_de_outra_obra(self):
        resp = self.client.get(f'/medicao/equip/{self.outra_obra.id}/periodos/')
        self.assertContains(resp, 'Acesso negado')
