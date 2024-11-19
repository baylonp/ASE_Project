from locust import HttpUser, task, between
import random
import string

class AuthServiceUser(HttpUser):
    wait_time = between(1, 3)  # Attesa tra una richiesta e l'altra

    @task
    def run_all_tasks_in_order(self):
        # 1. Creazione dell'account
        self.username = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.email = f"{self.username}@example.com"
        self.password = "password123"

        response = self.client.post("/authentication/account", json={
            "username": self.username,
            "password": self.password,
            "email": self.email
        })

        if response.status_code == 201:
            # 2. Recuperare userId con username
            user_id_response = self.client.get("/authentication/userId", params={"username": self.username})
            if user_id_response.status_code == 200:
                self.user_id = user_id_response.json().get('userId')

                # 3. Login
                self.client.post("/authentication/auth", json={
                    "username": self.username,
                    "password": self.password
                })

                # 4. Aggiornare l'account (ad esempio l'email)
                new_email = f"updated_{self.email}"
                self.client.patch(f"/authentication/account", params={"accountId": self.user_id}, json={
                    "email": new_email
                })

                # 5. Aggiungere monete al wallet dell'utente
                self.client.post(f"/authentication/players/{self.user_id}/currency/add", params={"amount": 50})

                # 6. Sottrarre monete dal wallet dell'utente
                self.client.patch(f"/authentication/players/{self.user_id}/currency/subtract", json={"amount": 10})

                # 7. Recuperare tutte le informazioni dell'utente
                self.client.get(f"/authentication/players/{self.user_id}")

                # 8. Aggiornare la valuta dell'utente (può essere positivo o negativo)
                self.client.patch(f"/authentication/players/{self.user_id}/currency/update", json={"amount": 20})

                # 9. Cancellare l'account (eseguiamo alla fine per lasciare pulito il test)
                self.client.delete(f"/authentication/account", params={"accountId": self.user_id})

    def on_stop(self):
        # Questo metodo viene chiamato quando l'utente virtuale termina
        # Se l'account non è stato cancellato, lo eliminiamo per pulizia
        if hasattr(self, 'user_id'):
            self.client.delete(f"/authentication/account", params={"accountId": self.user_id})