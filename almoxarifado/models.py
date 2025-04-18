import os
import uuid
from datetime import datetime
from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django import forms


# ------------------- USUÁRIO PERSONALIZADO -------------------
class CustomUser(AbstractUser):
    PERFIL_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('almoxarife_cadastrado', 'Almoxarife Cadastrado'),
    ]
    categoria = models.CharField(
        max_length=30,
        choices=PERFIL_CHOICES,
        default='almoxarife_cadastrado'
    )

    def __str__(self):
        return f'{self.username} ({self.get_categoria_display()})'

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


# ------------------- FUNÇÃO PARA NOMEAR IMAGENS -------------------
def caminho_imagem_item(instance, filename):
    nome_base, extensao = os.path.splitext(filename)
    codigo_item = slugify(instance.item.codigo if instance.item and instance.item.codigo else 'sem_codigo')
    novo_nome = f"{slugify(nome_base)}-{uuid.uuid4()}{extensao}"
    return f"itens/{codigo_item}/{novo_nome}"


# ------------------- MODELO DE ITEM -------------------
class Item(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    quantidade = models.FloatField(default=0)
    criado_por = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='itens_cadastrados'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['codigo']


# ------------------- MODELO DE FOTOS DO ITEM -------------------
class FotoItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to=caminho_imagem_item)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Imagem do item {self.item.codigo}"

    class Meta:
        verbose_name = 'Foto do Item'
        verbose_name_plural = 'Fotos dos Itens'


# ------------------- FORMULÁRIO DE FOTO -------------------
class FotoItemForm(forms.ModelForm):
    class Meta:
        model = FotoItem
        fields = ['imagem']


# ------------------- MODELO DE VISUALIZAÇÃO DO SISTEMA -------------------
class VisualizacaoSistema(models.Model):
    data = models.DateTimeField(default=now)

    class Meta:
        verbose_name = 'Visualização do Sistema'
        verbose_name_plural = 'Visualizações do Sistema'


# ------------------- MODELO DE LOG DO SISTEMA -------------------

class LogSistema(models.Model):
    usuario = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_realizados'
    )
    acao = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "Desconhecido"
        return f"[{self.data.strftime('%d/%m/%Y %H:%M:%S')}] {usuario_str} - {self.acao}"
