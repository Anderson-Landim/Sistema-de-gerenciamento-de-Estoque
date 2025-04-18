from django.shortcuts import redirect
from functools import wraps

def perfil_required(*perfis_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # Verifica se o usuário está autenticado e tem o atributo 'categoria'
            if user.is_authenticated and hasattr(user, 'categoria'):
                if user.categoria in perfis_permitidos:
                    return view_func(request, *args, **kwargs)

            # Redireciona se não estiver autenticado ou não tiver permissão
            return redirect('acesso_negado')
        return _wrapped_view
    return decorator
