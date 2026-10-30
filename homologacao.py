from django.http import HttpResponseBadRequest

class IsolamentoHomologacaoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.path_info.startswith('/homologacao/'):
            return HttpResponseBadRequest('O proxy deve retirar o prefixo /homologacao/ ao encaminhar a solicitação.')
        response = self.get_response(request)
        response['X-Kaito-Ambiente'] = 'homologacao'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
