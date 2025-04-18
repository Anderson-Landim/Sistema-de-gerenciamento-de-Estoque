# ------------------- IMPORTAÇÕES GERAIS -------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, FileResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.timezone import make_aware, now, timedelta
from django.core.files.storage import FileSystemStorage
from django.contrib.sessions.models import Session
import tempfile
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


import ping3
from ping3 import ping 
from datetime import datetime
import os
import shutil
import openpyxl
import subprocess
import threading
import time
import platform
import re
import requests
import random




from .models import CustomUser, FotoItem, Item, VisualizacaoSistema, LogSistema
from .forms import AlmoxarifeForm, ItemForm, MultiFotoForm
from .decorators import perfil_required

# ------------------- PÁGINAS PÚBLICAS -------------------
def suporte(request):
    return render(request, "suporte.html")


def index(request):
    return render(request, "pagina_inicial.html")


# ------------------- AUTENTICAÇÃO -------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        hora_local = request.POST.get("hora_local")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hora_local:
                try:
                    user.last_login = make_aware(datetime.fromisoformat(hora_local))
                    user.save(update_fields=["last_login"])
                except Exception as e:
                    print("Erro ao converter hora_local:", e)
            return redirect("dashboard")
        else:
            return render(request, "login.html", {"error": "Usuário ou senha inválidos"})
    return render(request, "login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')


# ------------------- DASHBOARD -------------------
@login_required
def dashboard(request):
    return render(request, "dashboard.html")

@login_required
def dashboard_view(request):
    user = request.user
    if user.categoria == 'super_admin':
        return render(request, 'dashboard_super_admin.html')
    elif user.categoria == 'almoxarife_cadastrado':
        return render(request, 'dashboard_almoxarife.html')
    return render(request, 'acesso_negado.html')


# ------------------- GERENCIAMENTO DE USUÁRIOS -------------------
@login_required
@perfil_required('super_admin')
def gerenciar_usuarios(request):
    usuarios = CustomUser.objects.prefetch_related('itens_cadastrados').annotate(
        total_itens=Count('itens_cadastrados')
    )
    return render(request, 'gerenciar_usuarios.html', {'usuarios': usuarios})

@login_required
@perfil_required('super_admin')
def cadastrar_almoxarife(request):
    form = AlmoxarifeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('gerenciar_usuarios')
    return render(request, 'cadastrar_almoxarife.html', {'form': form})

@login_required
@perfil_required('super_admin')
def listar_almoxarifes(request):
    usuarios = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'listar_usuarios.html', {'usuarios': usuarios})

@login_required
@perfil_required('super_admin')
def remover_usuario(request, user_id):
    usuario = get_object_or_404(CustomUser, id=user_id)
    if usuario.id == request.user.id:
        messages.error(request, "Você não pode remover a si mesmo.")
    else:
        usuario.delete()
    return redirect('listar_usuarios')


# ------------------- PERMISSÕES -------------------
def permissao_para_cadastrar(user):
    return user.is_authenticated and user.categoria in ['super_admin', 'almoxarife_cadastrado']

def is_staff(user):
    return user.is_authenticated and user.is_staff


# ------------------- CADASTRO E EDIÇÃO DE ITENS -------------------
@login_required
@user_passes_test(permissao_para_cadastrar)
def cadastrar_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.criado_por = request.user
            item.save()

            LogSistema.objects.create(
                usuario=request.user,
                acao=f"Item '{item.nome}' (código: {item.codigo}) cadastrado."
            )

            imagens = request.FILES.getlist('imagens')
            for imagem in imagens:
                FotoItem.objects.create(item=item, imagem=imagem)

            if imagens:
                messages.success(request, "Item cadastrado com sucesso com imagens.")
            else:
                messages.warning(request, "Item cadastrado, mas nenhuma imagem foi enviada.")
            return redirect('cadastrar_item')
        else:
            messages.error(request, "Erro ao salvar o item.")
    else:
        form = ItemForm()
    return render(request, 'almoxarifado/cadastrar_item.html', {'item_form': form})


@login_required
@user_passes_test(permissao_para_cadastrar)
def editar_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    imagens = item.fotos.all()
    form = ItemForm(request.POST or None, request.FILES or None, instance=item)

    antigo_codigo = item.codigo  # Salva o código antes de editar

    if request.method == 'POST' and form.is_valid():
        item_editado = form.save(commit=False)
        novo_codigo = item_editado.codigo

        if novo_codigo != antigo_codigo:
            # Caminhos antigos e novos
            pasta_antiga = os.path.join(settings.MEDIA_ROOT, 'itens', antigo_codigo)
            pasta_nova = os.path.join(settings.MEDIA_ROOT, 'itens', novo_codigo)

            # Cria nova pasta se não existir
            os.makedirs(pasta_nova, exist_ok=True)

            for foto in imagens:
                caminho_antigo = foto.imagem.path
                nome_arquivo = os.path.basename(caminho_antigo)
                caminho_novo = os.path.join(pasta_nova, nome_arquivo)

                # Copia imagem para a nova pasta
                shutil.copy2(caminho_antigo, caminho_novo)

                # Atualiza o campo da imagem no banco
                novo_caminho_relativo = os.path.join('itens', novo_codigo, nome_arquivo)
                foto.imagem.name = novo_caminho_relativo
                foto.save()

            # Apaga pasta antiga
            if os.path.exists(pasta_antiga):
                shutil.rmtree(pasta_antiga)

        item_editado.save()
        LogSistema.objects.create(usuario=request.user, acao=f"Item '{item_editado.nome}' (código: {item_editado.codigo}) atualizado.")


        # Remover imagens
        ids_remover = request.POST.getlist('remover_imagens')
        if ids_remover:
            fotos_para_remover = FotoItem.objects.filter(id__in=ids_remover)
            for foto in fotos_para_remover:
                if foto.imagem and foto.imagem.path and os.path.isfile(foto.imagem.path):
                    os.remove(foto.imagem.path)
                foto.delete()

        # Novas imagens
        novas_imagens = request.FILES.getlist('novas_imagens')
        for imagem in novas_imagens:
            FotoItem.objects.create(item=item_editado, imagem=imagem)

        messages.success(request, 'Item atualizado com sucesso!')
        return redirect('listar_itens')

    return render(request, 'almoxarifado/editar_item.html', {
        'form': form,
        'item': item,
        'imagens': imagens,
    })



@login_required
@user_passes_test(permissao_para_cadastrar)
def remover_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    codigo = item.codigo
    nome = item.nome

    # LOG: salva antes de deletar
    LogSistema.objects.create(
        usuario=request.user,
        acao=f"Item excluído: {codigo} | Nome: {nome}"
    )

    # Remove o item e a pasta de imagens
    item.delete()
    pasta_item = os.path.join(settings.MEDIA_ROOT, 'itens', codigo)
    if os.path.exists(pasta_item):
        shutil.rmtree(pasta_item)

    messages.success(request, f'Item "{codigo}" removido com sucesso.')
    return redirect('listar_itens')  # Certifique-se de redirecionar corretamente



# ------------------- LISTAGEM E BUSCA DE ITENS -------------------
@login_required
@user_passes_test(permissao_para_cadastrar)
def listar_itens(request):
    busca = request.GET.get("busca", "").strip()
    itens_list = Item.objects.prefetch_related('fotos')

    if busca:
        itens_list = itens_list.filter(
            Q(nome__icontains=busca) |
            Q(codigo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(quantidade__icontains=busca)
        )

    itens_list = itens_list.order_by('-id')
    paginator = Paginator(itens_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🔥 Se for busca via AJAX (JS), retorna apenas os cards!
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'almoxarifado/parcial_item.html', {'itens': page_obj})

    # 🔁 Se for a página normal
    return render(request, 'almoxarifado/listar_itens.html', {'itens': page_obj})


# ------------------- PÁGINAS DE ERRO / ACESSO -------------------
def acesso_negado(request):
    return render(request, 'acesso_negado.html')

def sem_permissao(request):
    return render(request, 'sem_permissao.html')

# ------------------- Catalogo Publico -------------------

def catalogo_publico(request):
    busca = request.GET.get('busca', '')
    page = request.GET.get('page', 1)

    if busca:
        itens = Item.objects.filter(
            Q(nome__icontains=busca) |
            Q(codigo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(quantidade__icontains=busca)
        ).order_by('-id')
    else:
        itens = Item.objects.all().order_by('-id')

    paginator = Paginator(itens, 20)
    page_obj = paginator.get_page(page)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'almoxarifado/parcial_item.html', {'itens': page_obj})

    return render(request, 'almoxarifado/catalogo_publico.html', {'itens': page_obj})

# ------------------- importar excel -------------------

@login_required
@user_passes_test(permissao_para_cadastrar)
def importar_excel(request):
    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']
        if not arquivo.name.endswith('.xlsx'):
            messages.error(request, "Por favor envie um arquivo .xlsx válido.")
            return redirect('importar_excel')

        try:
            wb = openpyxl.load_workbook(arquivo)
        except Exception as e:
            messages.error(request, f"Erro ao ler o arquivo: {str(e)}")
            return redirect('importar_excel')

        planilha = wb.active

        contagem_novos = 0

        for linha in planilha.iter_rows(min_row=2, values_only=True):
            if linha is None or all(cell is None for cell in linha):
                continue

            if len(linha) == 4:
                codigo, nome_item, descricao, quantidade = linha
            elif len(linha) == 3:
                codigo, nome_item, quantidade = linha
                descricao = ""
            else:
                continue

            if not codigo:
                continue

            try:
                quantidade = float(quantidade)
            except:
                quantidade = 0

            item, criado = Item.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nome': nome_item or 'Sem nome',
                    'descricao': descricao or '',
                    'quantidade': quantidade,
                    'criado_por': request.user,
                }
            )

            if not criado:
                item.nome = nome_item or item.nome
                item.quantidade = quantidade  # sobrescreve
                if descricao:  # Só atualiza se veio algo no Excel
                    item.descricao = descricao
                item.save()
                
            else:
                contagem_novos += 1

        messages.success(
            request,
            f"Importação concluída. Novos: {contagem_novos}"
        )

        LogSistema.objects.create(
            usuario=request.user,
            acao=f"Importação concluída: {contagem_novos} novos,"
        )

        return redirect('importar_excel')

    return render(request, 'almoxarifado/importar_excel.html')



# ------------------- ESTATÍSTICAS -------------------


@login_required
@perfil_required('super_admin')
def estatisticas(request):
    total_visualizacoes = VisualizacaoSistema.objects.count()
    total_itens = Item.objects.count()

    # Usuários online (sessões não expiradas nas últimas 15 min)
    tempo_limite = now() - timedelta(minutes=15)
    sessoes_ativas = Session.objects.filter(expire_date__gte=now())
    usuarios_online = 0
    for sessao in sessoes_ativas:
        dados = sessao.get_decoded()
        if '_auth_user_id' in dados:
            usuarios_online += 1

    logs = LogSistema.objects.order_by('-data')[:100]  # últimos 100 logs

    return render(request, 'dashboard_super_admin.html', {
        'total_visualizacoes': total_visualizacoes,
        'total_itens': total_itens,
        'usuarios_online': usuarios_online,
        'logs': logs,
    })

"""@login_required
@perfil_required('super_admin')
def exportar_logs_txt(request):
    logs = LogSistema.objects.all().order_by('data')

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
        for log in logs:
            f.write(f"{log}\n")
        f.seek(0)
        return FileResponse(open(f.name, 'rb'), as_attachment=True, filename='log_sistema.txt')"""




@login_required
@perfil_required('super_admin')
def estatisticas_gerais(request):
    # Total de itens cadastrados
    total_itens = Item.objects.count()

    # Itens por usuário
    itens_por_usuario = CustomUser.objects.annotate(
        total=Count('itens_cadastrados')
    ).filter(total__gt=0)

    # Último item cadastrado
    ultimo_item = Item.objects.order_by('-id').first()

    # Logs de ações (últimos 10 de cada tipo)
    logs_importacao = LogSistema.objects.filter(
        acao__icontains='Importação concluída'
    ).order_by('-data')[:10]

    logs_cadastro = LogSistema.objects.filter(
        Q(acao__icontains='cadastrado') & Q(acao__icontains='Item')
    ).order_by('-data')[:10]

    logs_edicao = LogSistema.objects.filter(
        Q(acao__icontains='atualizado') & Q(acao__icontains='Item')
    ).order_by('-data')[:10]

    logs_exclusao = LogSistema.objects.filter(
        Q(acao__icontains='Item excluído') | Q(acao__icontains='excluído')
    ).order_by('-data')[:10]

    # Estatísticas de visualização
    agora = now()
    total_visualizacoes = VisualizacaoSistema.objects.count()
    visualizacoes_24h = VisualizacaoSistema.objects.filter(data__gte=agora - timedelta(hours=24)).count()
    visualizacoes_semana = VisualizacaoSistema.objects.filter(data__gte=agora - timedelta(days=7)).count()
    visualizacoes_mes = VisualizacaoSistema.objects.filter(data__gte=agora - timedelta(days=30)).count()

    return render(request, 'estatisticas/estatisticas_geral.html', {
        'total_itens': total_itens,
        'itens_por_usuario': itens_por_usuario,
        'ultimo_item': ultimo_item,
        'logs_importacao': logs_importacao,
        'logs_cadastro': logs_cadastro,
        'logs_edicao': logs_edicao,
        'logs_exclusao': logs_exclusao,
        'total_visualizacoes': total_visualizacoes,
        'visualizacoes_24h': visualizacoes_24h,
        'visualizacoes_semana': visualizacoes_semana,
        'visualizacoes_mes': visualizacoes_mes,
    })


def teste_performance(request):
    log_path = os.path.join(settings.BASE_DIR, "locust_log.txt")

    # Executa o Locust como linha de comando em modo headless
    comando = [
        "locust",
        "-f", os.path.join(settings.BASE_DIR, "locustfile.py"),
        "--headless",
        "-u", "50",  # 50 usuários simultâneos
        "-r", "5",   # 5 usuários novos por segundo
        "-t", "10s",  # duração do teste: 10 segundos
        "--csv", os.path.join(settings.BASE_DIR, "locust_resultado"),
        "--only-summary",
        "--host", "http://127.0.0.1:8000/"
    ]

    try:
        resultado = subprocess.run(comando, capture_output=True, text=True)
        with open(log_path, "w") as f:
            f.write(resultado.stdout)
    except Exception as e:
        return render(request, "teste_resultado.html", {
            "erro": str(e)
        })

    # Leitura dos resultados
    with open(log_path, "r") as f:
        output = f.read()

    return render(request, "teste_resultado.html", {
        "output": output
    })


# Variável global para armazenar o status do teste
resultado_teste_info = {"output": None, "erro": None, "finalizado": False}
teste_evento = threading.Event()

@csrf_exempt
def iniciar_teste(request):
    """
    Inicia o teste de conexão HTTP com o servidor local e realiza também o teste de ping.
    A execução do teste ocorre em uma thread separada para não bloquear o servidor.
    """
    global resultado_teste_info
    resultado_teste_info = {"output": None, "erro": None, "finalizado": False}

    def executar_teste():
        global resultado_teste_info
        try:
            url = "http://127.0.0.1:8000/"  # URL do servidor local
            total_requisicoes = 0
            max_requisicoes = int(random.uniform(5, 25))  # Número máximo de requisições a serem feitas no teste

            # Teste de Conexão HTTP
            while total_requisicoes < max_requisicoes:
                resposta = requests.get(url)
                total_requisicoes += 1

                if resposta.status_code == 200:
                    resultado_teste_info["output"] = f"Conexão HTTP bem-sucedida com o servidor. Requisições realizadas: {total_requisicoes}"
                    resultado_teste_info["erro"] = None
                    resultado_teste_info["finalizado"] = False  # Indica que o teste HTTP ainda não foi finalizado
                else:
                    resultado_teste_info = {
                        "output": None,
                        "erro": f"Erro ao conectar com o servidor. Status: {resposta.status_code}",
                        "finalizado": True
                    }
                    break

                time.sleep(1)  # Aguarda 1 segundo antes de fazer a próxima requisição

            # Quando atingir o máximo de requisições, finaliza o teste HTTP
            if total_requisicoes >= max_requisicoes:
                resultado_teste_info["finalizado"] = True

            # Teste de Ping (usando ping3)
            try:
                resposta_ping = ping('127.0.0.1', timeout=1)  # Timeout de 1 segundo
                if resposta_ping is not None:
                    resultado_teste_info["ping_output"] = f"Ping bem-sucedido: {resposta_ping} ms"
                    resultado_teste_info["ping_erro"] = None
                else:
                    resultado_teste_info["ping_output"] = None
                    resultado_teste_info["ping_erro"] = "Erro ao realizar o ping: Sem resposta do servidor"
            except Exception as e:
                resultado_teste_info["ping_output"] = None
                resultado_teste_info["ping_erro"] = f"Erro ao realizar o ping: {str(e)}"
            
            # dentro de executar_teste() — após o teste de ping
            try:
                if resposta_ping is not None and resposta_ping > 0:
                    max_requisicoes = int(random.uniform(5, 25))
                    estimativa_rps = int(1 / resposta_ping)  # RTT já está em segundos
                    resultado_teste_info["rtt"] = resposta_ping
                    resultado_teste_info["estimativa_rps"] = estimativa_rps
                else:
                    resultado_teste_info["rtt"] = None
                    resultado_teste_info["estimativa_rps"] = None
            except Exception as e:
                resultado_teste_info["rtt"] = None
                resultado_teste_info["estimativa_rps"] = None

            
            # Analisando o resultado do ping para pegar pacotes e tempo (se necessário)
            # Você pode adicionar lógica para extrair mais detalhes do resultado do ping, caso precise

        except requests.exceptions.RequestException as e:
            resultado_teste_info = {"output": None, "erro": str(e), "finalizado": True}
        except Exception as e:
            resultado_teste_info = {"output": None, "erro": str(e), "finalizado": True}
        finally:
            teste_evento.set()  # Notifica que o teste foi finalizado

    # Inicia o teste em uma thread separada
    threading.Thread(target=executar_teste, daemon=True).start()

    # Retorna uma página informando ao usuário que o teste está em andamento
    return render(request, "teste/aguarde.html")

def verificar_status(request):
    """
    Retorna o status do teste de conexão HTTP e ping em formato JSON.
    """
    if not resultado_teste_info["finalizado"]:
        teste_evento.wait()  # Espera até o teste ser finalizado

    return JsonResponse(resultado_teste_info)

def resultado_teste_view(request):
    output = resultado_teste_info.get("output")
    erro = resultado_teste_info.get("erro")
    ping_output = resultado_teste_info.get("ping_output")
    ping_erro = resultado_teste_info.get("ping_erro")
    rtt = resultado_teste_info.get("rtt")
    estimativa_rps = resultado_teste_info.get("estimativa_rps")

    dados = {
        "erro": erro,
        "output": output,
        "ping_output": ping_output,
        "ping_erro": ping_erro,
        "rtt": rtt,
        "estimativa_rps": estimativa_rps,
        "resumo": None,
    }

    if output:
        dados["resumo"] = {
            "tipo": "Conexão HTTP",
            "endpoint": "http://127.0.0.1:8000/",
            "sucesso": "Sim" if erro is None else "Não",
            "detalhes": output
        }

    if ping_output:
        dados["resumo_ping"] = ping_output

    print(f"Resultado do teste:", dados)

    return render(request, "teste/resultado.html", dados)


   