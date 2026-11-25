"""Idempotent validation of an explicit, immutable batch of field receipts."""
import hashlib
import json
from datetime import date
from uuid import UUID
from django.db import IntegrityError, OperationalError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from .models import ValidacaoResponsavelCampo, ReciboAbastecimentoCampo, Abastecimento
from .views_campo import _acesso, _assinatura


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


def resposta(obj,user,hash_conteudo):
    if obj.usuario_id!=user.pk or obj.hash_conteudo!=hash_conteudo:
        return JsonResponse({'erro':'Identificador de validação já utilizado com outros dados.'},status=409)
    return JsonResponse({'id':str(obj.pk),'quantidade':obj.abastecimentos.count(),'recebido_em':obj.recebido_em.isoformat()})


@require_POST
@never_cache
def enviar_validacao(request):
    denied=_acesso(request)
    if denied is not None: return denied
    try:
        if len(request.body)>4194304: raise ValueError()
        data=json.loads(request.body)
        ident=UUID(data['id'])
        if data['usuario_id']!=request.user.pk:
            return JsonResponse({'erro':'Entre com o usuário que registrou esta validação.','codigo':'usuario'},status=403)
        dia=date.fromisoformat(data['data'])
        obra=int(data['obra_id'])
        assinatura=_assinatura(data['assinatura'])
        if not assinatura: raise ValueError()
        responsavel=data.get('responsavel','').strip()
        if len(responsavel)>100: raise ValueError()
        registrado=parse_datetime(data['registrado_em'])
        if registrado is None or timezone.is_naive(registrado): raise ValueError()
        snapshots=data['registros']
        if not isinstance(snapshots,list) or not 1<=len(snapshots)<=1000: raise ValueError()
        hashes={}
        for row in snapshots:
            key=UUID(row['id'])
            payload=json.loads(row['conteudo'])
            if not isinstance(payload,dict) or UUID(payload['id'])!=key or key in hashes: raise ValueError()
            hashes[key]=digest(payload)
        hash_conteudo=digest(data)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,UnicodeError):
        return JsonResponse({'erro':'Confira obra, data, assinatura e os abastecimentos da validação.'},status=400)
    existing=ValidacaoResponsavelCampo.objects.filter(pk=ident).first()
    if existing: return resposta(existing,request.user,hash_conteudo)
    try:
        with transaction.atomic():
            recibos=list(ReciboAbastecimentoCampo.objects.select_for_update().filter(pk__in=hashes).select_related('abastecimento'))
            if len(recibos)!=len(hashes):
                return JsonResponse({'erro':'Sincronize todos os abastecimentos deste grupo antes da validação.','codigo':'aguardar'},status=425)
            ids=[]
            for recibo in recibos:
                r=recibo.abastecimento
                if recibo.usuario_id!=request.user.pk or r.colaborador_id!=request.user.pk:
                    return JsonResponse({'erro':'Este grupo contém lançamentos de outro usuário.'},status=403)
                if not request.user.is_superuser and r.tanque_id!=request.user.tanque_abastecimento_id:
                    return JsonResponse({'erro':'Tanque ou comboio não autorizado para este usuário.'},status=403)
                if r.obra_id!=obra or r.data!=dia or recibo.hash_conteudo!=hashes[recibo.pk]:
                    return JsonResponse({'erro':'Os abastecimentos mudaram ou não pertencem à mesma obra e dia. Faça uma nova validação.'},status=409)
                if r.validacao_responsavel_id:
                    return JsonResponse({'erro':'Um abastecimento deste grupo já foi validado. Atualize e valide somente os ainda não validados.'},status=409)
                ids.append(r.pk)
            obj=ValidacaoResponsavelCampo.objects.create(id=ident,usuario=request.user,obra_id=obra,data=dia,
                responsavel=responsavel,assinatura=assinatura,hash_conteudo=hash_conteudo,registrado_no_aparelho=registrado)
            count=Abastecimento.objects.filter(pk__in=ids,validacao_responsavel__isnull=True).update(validacao_responsavel=obj)
            if count!=len(ids): raise IntegrityError('Concurrent validation')
        return resposta(obj,request.user,hash_conteudo)
    except IntegrityError:
        existing=ValidacaoResponsavelCampo.objects.filter(pk=ident).first()
        if existing: return resposta(existing,request.user,hash_conteudo)
        return JsonResponse({'erro':'O grupo foi alterado por outra validação. Tente novamente.'},status=409)
    except OperationalError:
        return JsonResponse({'erro':'Servidor ocupado. A validação continua no aparelho.'},status=503)
