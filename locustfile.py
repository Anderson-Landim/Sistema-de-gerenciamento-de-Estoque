from locust import HttpUser, task, between

class PublicUser(HttpUser):
    host = "http://127.0.0.1:8000"  # Defina o host para o seu Django

    wait_time = between(1, 2)  # Intervalo entre as requisições

    @task
    def index(self):
        self.client.get("/")  # Acessa a página principal (index)

    @task
    def catalogo(self):
        self.client.get("/catalogo/")  # Acessa a página do catálogo
