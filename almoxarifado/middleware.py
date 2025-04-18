import hashlib
from django.utils.deprecation import MiddlewareMixin
from .models import VisualizacaoSistema

class ContadorVisualizacoesMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            return  # Não conta usuários logados

        # Cria identificador único por IP + User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip = request.META.get('REMOTE_ADDR', '')
        identificador = hashlib.sha256(f"{ip}-{user_agent}".encode()).hexdigest()

        # Define o nome do cookie
        cookie_key = f'visitado_{identificador}'

        # Se o cookie não existe, registra visualização
        if not request.COOKIES.get(cookie_key):
            request._set_visita_cookie = cookie_key

    def process_response(self, request, response):
        if hasattr(request, '_set_visita_cookie'):
            # Define cookie por 24 horas
            response.set_cookie(request._set_visita_cookie, '1', max_age=60*60*24)
        return response
