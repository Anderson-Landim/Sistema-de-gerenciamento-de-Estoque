#!/bin/bash

# Caminho do projeto Django (ajuste conforme necessário)
cd "/home/seu_usuario/caminho/para/Sistema de Visualização de Estoque/estoque"

# Ativar ambiente virtual (se estiver usando)
# source venv/bin/activate  # Descomente e ajuste se necessário

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Iniciar o servidor
echo "Iniciando servidor em 0.0.0.0:8000..."
python3 manage.py runserver 0.0.0.0:8000
