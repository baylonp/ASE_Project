from locust import HttpUser, task, between
import random
import string

class AuthServiceUser(HttpUser):
    wait_time = between(1, 3)  # Wait time between requests

    def on_start(self):
        # This method is called when the virtual user starts
        self.jwt_token = None
        
        # Disable SSL Verification
        self.client.verify = False

    @task
    def run_all_tasks_in_order(self):

        # 1. Create the account
        self.username = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.email = f"{self.username}@example.com"
        self.password = "1022222"

        response = self.client.post("/authentication/account", json={
            "username": self.username,
            "password": self.password,
            "email": self.email
        })

        if response.status_code == 201:
                # 2. Login to get the JWT token
                login_response = self.client.post("/authentication/auth", json={
                    "username": self.username,
                    "password": self.password
                })
                if login_response.status_code == 200:
                    # the JWT token is returned in the response body
                    self.jwt_token = login_response.json().get("token")
                    
                    # 4. Now use the JWT token for subsequent requests
                    if self.jwt_token:
                        self.client.headers.update({"x-access-token": str(self.jwt_token)})

                        # 5. Get userId with username
                        user_id_response = self.client.get("/authentication/userId", params={"username": self.username})
                        if user_id_response.status_code == 200:
                         self.user_id = user_id_response.json().get('userId')

                        # 6. Update account (e.g., change email)
                        new_email = f"updated_{self.email}"
                        self.client.patch(f"/authentication/account", params={"accountId": self.user_id}, json={
                            "email": new_email
                        })

                        # 7. Add coins to the wallet
                        self.client.post(f"/authentication/players/{self.user_id}/currency/add", params={"amount": 100})

                        # 8. Subtract coins from the wallet
                        self.client.patch(f"/authentication/players/{self.user_id}/currency/subtract", json={"amount": 10})

                        # 9. Retrieve all player info
                        self.client.get(f"/authentication/players/{self.user_id}")

                        # 10. Update the player's currency
                        self.client.patch(f"/authentication/players/{self.user_id}/currency/update", json={"amount": 20})

                        # 11. Delete the account (cleanup)
                        self.client.delete(f"/authentication/account", params={"accountId": self.user_id})

    def on_stop(self):
        # This method is called when the user virtual user stops
        # If the account was not deleted, remove it for cleanup
        if hasattr(self, 'user_id'):
            self.client.delete(f"/authentication/account", params={"accountId": self.user_id})