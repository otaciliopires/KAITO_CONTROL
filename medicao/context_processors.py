from django.conf import settings


def medicao_flags(request):
    return {'medicao_habilitado': 'medicao' in settings.INSTALLED_APPS}
