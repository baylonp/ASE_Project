from locust import HttpUser, TaskSet, task, between
import random

class AuthenticationTasks(TaskSet):

    @task(1)
    def create_account(self):
        """
        Task per la creazione di un account.
        Genera un nuovo account con un username univoco.
        """
        username = f"testuser_{random.randint(1, 100)}"
        response = self.client.post("/account", json={
            "username": username,
            "password": "testpassword",
            "email": f"{username}@example.com"
        })
        if response.status_code == 201:
            print(f"Account created successfully: {username}")
        else:
            print(f"Failed to create account: {response.status_code} - {response.text}")

    @task(2)
    def login(self):
        """
        Task per il login dell'utente.
        Utilizza credenziali di test predefinite.
        """
        response = self.client.post("/auth", json={
            "username": "testuser_1",  
            "password": "testpassword"
        })
        if response.status_code == 200:
            print(f"Login successful for user: testuser_1")
        else:
            print(f"Failed login attempt: {response.status_code} - {response.text}")

    @task(1)
    def delete_account(self):
        """
        Task per la cancellazione di un account.
        Prova a cancellare un account con un ID fittizio.
        """
        account_id = random.randint(1, 100)
        response = self.client.delete("/account", params={"accountId": str(account_id)})
        if response.status_code == 200:
            print(f"Account deleted successfully: {account_id}")
        elif response.status_code == 404:
            print(f"Account not found: {account_id}")
        else:
            print(f"Failed to delete account: {response.status_code} - {response.text}")

    @task(1)
    def login_invalid_credentials(self):
        """
        Task per il login con credenziali non valide.
        """
        response = self.client.post("/auth", json={
            "username": "invaliduser",
            "password": "wrongpassword"
        })
        if response.status_code == 401:
            print("Invalid credentials, as expected.")
        else:
            print(f"Unexpected response for invalid credentials: {response.status_code} - {response.text}")

class WebsiteUser(HttpUser):
    tasks = [AuthenticationTasks]
    wait_time = between(1, 2)  # Tempo di attesa tra ogni task per ogni utente (tra 1 e 2 secondi)
