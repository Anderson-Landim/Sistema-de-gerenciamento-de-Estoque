from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('suporte/', views.suporte, name='suporte'),
    path('sem-permissao/', views.sem_permissao, name='sem_permissao'),
    path('gerenciar-usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
    path('acesso-negado/', views.acesso_negado, name='acesso_negado'),
    path('dashboard-super-admin/', views.dashboard_view, name='dashboard_super_admin'),
    path('cadastrar-usuario/', views.cadastrar_almoxarife, name='cadastrar_almoxarife'),
    path('listar-usuarios/', views.listar_almoxarifes, name='listar_almoxarifes'),
    path('usuarios/remover/<int:user_id>/', views.remover_usuario, name='remover_usuario'),
    path('usuarios/', views.listar_almoxarifes, name='listar_usuarios'),
    path('cadastrar-item/', views.cadastrar_item, name='cadastrar_item'),
    path('itens/', views.listar_itens, name='listar_itens'),
    path('listar-itens/', views.listar_itens, name='listar_itens'),
    path('remover-item/<int:item_id>/', views.remover_item, name='remover_item'),
    path('editar-item/<int:item_id>/', views.editar_item, name='editar_item'),
    path("catalogo/", views.catalogo_publico, name="catalogo_publico"),
    path('importar-excel/', views.importar_excel, name='importar_excel'),
    path('estatisticas/geral/', views.estatisticas_gerais, name='estatisticas_gerais'),
    path("teste-performance/", views.teste_performance, name="teste_performance"),
    path("teste/", views.iniciar_teste, name="iniciar_teste"),
    path("teste/status/", views.verificar_status, name="verificar_status"),
    path("teste/resultado/", views.resultado_teste_view, name="resultado_teste"),







] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)