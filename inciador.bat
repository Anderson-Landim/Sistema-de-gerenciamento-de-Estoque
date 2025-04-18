
:: Caminho do projeto Django (ajuste conforme necessário)
C:\Users\Ander\OneDrive\Desktop\Sistema de Visualição de Estoque\estoque


:: Instalar dependências
echo Instalando dependencias...
pip install -r requirements.txt

:: Iniciar o servidor
echo Iniciando servidor em 0.0.0.0:8000...
python manage.py runserver 0.0.0.0:8000

pause
