"""Field fueling: isolated offline shell, scoped catalogs and idempotent ingestion."""
import hashlib
import json
import math
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.conf import settings
from django.contrib.staticfiles import finders
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Max, Sum
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.templatetags.static import static
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from ativos.models import Obras, Equipamentos
from .models import Tanque, Abastecimento, Entrada, Transferencia, ReciboAbastecimentoCampo


def _acesso(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'erro': 'Entre novamente para sincronizar.', 'codigo': 'login'}, status=401)
    if not user.is_active or not (user.is_superuser or user.status == 'a'):
        return JsonResponse({'erro': 'Usuário sem acesso ao abastecimento em campo.'}, status=403)
    if not user.is_superuser and not user.tanque_abastecimento_id:
        return JsonResponse({'erro': 'Peça ao administrador para vincular seu tanque ou comboio.'}, status=403)


@require_GET
def app_campo(request):
    # Public shell contains no user information, passwords or business records.
    return render(request, 'campo.html', {'ambiente_homologacao': getattr(settings, 'AMBIENTE_HOMOLOGACAO', False)})


@require_GET
@never_cache
def service_worker(request):
    path = finders.find('campo/sw.js')
    with open(path, encoding='utf-8') as stream:
        return HttpResponse(stream.read(), content_type='application/javascript')


@require_GET
def manifest(request):
    base = reverse('campo')
    teste = getattr(settings, 'AMBIENTE_HOMOLOGACAO', False)
    return JsonResponse({'id': base, 'name': 'KAITO · Campo · HOMOLOGAÇÃO' if teste else 'KAITO · Abastecimento em campo',
        'short_name': 'KAITO Teste' if teste else 'KAITO Campo', 'start_url': base, 'scope': base,
        'display': 'standalone', 'theme_color': '#20573d', 'background_color': '#f2f6f3',
        'icons': [{'src': static('campo/icon.svg'), 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any'}]},
        content_type='application/manifest+json')


@require_GET
@never_cache
def cadastros(request):
    denied = _acesso(request)
    if denied is not None:
        return denied
    user = request.user
    tanques = Tanque.objects.all() if user.is_superuser else Tanque.objects.filter(pk=user.tanque_abastecimento_id)
    return JsonResponse({'usuario': {'id': user.pk, 'nome': user.get_full_name() or user.username},
        'tanques': list(tanques.order_by('prefixo').values('id', 'prefixo')),
        'obras': list(Obras.objects.order_by('nome').values('id', 'nome')),
        'equipamentos': list(Equipamentos.objects.order_by('prefixo').values('id', 'prefixo', 'descricao')),
        'csrf': get_token(request), 'atualizado_em': timezone.now().isoformat()})


def _numero(valor):
    if isinstance(valor, bool):
        raise ValueError('Leitura inválida.')
    texto = str(valor).strip()
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    n = Decimal(texto)
    if not n.is_finite() or n < 0 or n > Decimal('1000000000000'):
        raise ValueError('Leituras devem ser positivas ou zero, dentro do limite permitido.')
    return n


def _assinatura(value):
    if value == {}:
        return {}
    if not isinstance(value, dict) or set(value) != {'versao', 'tracos'} or value['versao'] != 1:
        raise ValueError('Assinatura inválida.')
    tracos = value['tracos']
    if not isinstance(tracos, list) or not 1 <= len(tracos) <= 64:
        raise ValueError('Assinatura inválida.')
    total = 0
    for traco in tracos:
        if not isinstance(traco, list) or len(traco) < 2:
            raise ValueError('Assinatura inválida.')
        total += len(traco)
        if total > 1500:
            raise ValueError('Assinatura muito longa.')
        for ponto in traco:
            if not isinstance(ponto, list) or len(ponto) != 2:
                raise ValueError('Assinatura inválida.')
            for coordenada in ponto:
                if isinstance(coordenada, bool) or not isinstance(coordenada, (int, float)) or not math.isfinite(coordenada) or not 0 <= coordenada <= 1:
                    raise ValueError('Assinatura inválida.')
    return value


def _recibo(recibo, user, digest):
    if recibo.usuario_id != user.pk or recibo.hash_conteudo != digest:
        return JsonResponse({'erro': 'Este identificador já foi usado com outros dados. O registro não foi reenviado.'}, status=409)
    return JsonResponse({'id': str(recibo.pk), 'abastecimento_id': recibo.abastecimento_id,
        'numero': recibo.abastecimento.numero, 'recebido_em': recibo.recebido_em.isoformat()})


@require_POST
@never_cache
def enviar(request):
    denied = _acesso(request)
    if denied is not None:
        return denied
    try:
        if len(request.body) > 131072:
            raise ValueError('Lançamento muito grande.')
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError('Lançamento inválido.')
        operation_id = UUID(data['id'])
        if data.get('usuario_id') != request.user.pk:
            return JsonResponse({'erro': 'Entre com o mesmo usuário que registrou este abastecimento.', 'codigo': 'usuario'}, status=403)
        tanque_id = int(data['tanque_id'])
        if not request.user.is_superuser and tanque_id != request.user.tanque_abastecimento_id:
            return JsonResponse({'erro': 'Este tanque não está mais autorizado para seu usuário. Procure o administrador.'}, status=403)
        inicio, fim, horimetro = (_numero(data[k]) for k in ('contador_inicio', 'contador_fim', 'horimetro'))
        if fim <= inicio:
            raise ValueError('O contador final deve ser maior que o inicial.')
        dia = date.fromisoformat(data['data'])
        registrado = parse_datetime(data['registrado_em'])
        if registrado is None or timezone.is_naive(registrado):
            raise ValueError('Data de registro do aparelho inválida.')
        operador = data['operador'].strip()
        observacao = data.get('observacao', '').strip()
        if not operador or len(operador) > 50 or len(observacao) > 100:
            raise ValueError('Informe operador (até 50 caracteres) e observações (até 100).')
        if not isinstance(data.get('lubrificacao'), bool):
            raise ValueError('Informe se o veículo foi lubrificado.')
        assinatura = _assinatura(data.get('assinatura', {}))
        obra_id, equipamento_id = int(data['obra_id']), int(data['equipamento_id'])
        digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()
    except (KeyError, TypeError, ValueError, InvalidOperation, AttributeError, OverflowError, UnicodeError):
        return JsonResponse({'erro': 'Confira obra, equipamento, data, operador e leituras do lançamento.'}, status=400)
    existing = ReciboAbastecimentoCampo.objects.filter(pk=operation_id).first()
    if existing:
        return _recibo(existing, request.user, digest)
    try:
        with transaction.atomic():
            tanque = Tanque.objects.select_for_update().get(pk=tanque_id)
            obra = Obras.objects.select_for_update().get(pk=obra_id)
            equipamento = Equipamentos.objects.get(pk=equipamento_id)
            numero = (Abastecimento.objects.aggregate(n=Max('numero'))['n'] or 0) + 1
            abastecimento = Abastecimento.objects.create(numero=numero, litros=fim-inicio,
                contador_inicio=inicio, contador_fim=fim, horimetro=horimetro, data=dia,
                tanque=tanque, obra=obra, equipamento=equipamento, colaborador=request.user,
                operador=operador, lubrificacao=data['lubrificacao'], observacao=observacao, assinatura=assinatura)
            recibo = ReciboAbastecimentoCampo.objects.create(id=operation_id, usuario=request.user,
                abastecimento=abastecimento, hash_conteudo=digest, registrado_no_aparelho=registrado)
            def soma(qs, field):
                return qs.aggregate(n=Sum(field))['n'] or 0
            obra.saldo = soma(Entrada.objects.filter(obra=obra), 'quantidade') - soma(Abastecimento.objects.filter(obra=obra), 'litros')
            obra.save(update_fields=['saldo'])
            tanque.estoque = soma(Entrada.objects.filter(tanque=tanque), 'quantidade') + soma(Transferencia.objects.filter(movel=tanque), 'litros') - soma(Transferencia.objects.filter(fixo=tanque), 'litros') - soma(Abastecimento.objects.filter(tanque=tanque), 'litros')
            # A delayed upload must not roll the tank meter backwards.
            tanque.contador = max(float(fim), tanque.contador)
            tanque.save(update_fields=['estoque', 'contador'])
        return _recibo(recibo, request.user, digest)
    except (Tanque.DoesNotExist, Obras.DoesNotExist, Equipamentos.DoesNotExist):
        return JsonResponse({'erro': 'Um cadastro não existe mais. Atualize os cadastros e procure o administrador.'}, status=400)
    except IntegrityError:
        existing = ReciboAbastecimentoCampo.objects.filter(pk=operation_id).first()
        if existing:
            return _recibo(existing, request.user, digest)
        return JsonResponse({'erro': 'Não foi possível confirmar o lançamento. Tente sincronizar novamente.'}, status=503)
    except OperationalError:
        return JsonResponse({'erro': 'Servidor ocupado. O lançamento permanece no aparelho; tente novamente.'}, status=503)
