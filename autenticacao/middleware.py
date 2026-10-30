from django.http import JsonResponse
from django.shortcuts import redirect


class AbastecedorRestritoMiddleware:
    """Restrict field accounts even on legacy views without authorization checks."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and user.status == 'a':
            allowed = request.path_info.startswith(('/ceq/campo/', '/static/campo/')) or request.path_info in ('/auth/login/', '/auth/sair/')
            if not allowed:
                if request.method not in ('GET', 'HEAD') or request.path_info.startswith('/api/'):
                    return JsonResponse({'erro': 'Este usuário só tem acesso ao abastecimento em campo.'}, status=403)
                return redirect('campo')
        return self.get_response(request)
