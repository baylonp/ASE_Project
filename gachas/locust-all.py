from locust import HttpUser, task, between
import json
 
class F1DriversGachaUser(HttpUser):
    wait_time = between(1, 1)  # Nessun tempo casuale tra richieste
    
    def on_start(self):
        # This method is called when the virtual user starts
        self.jwt_token = None
        
        # Disable SSL Verification
        self.client.verify = False
 
    @task
    def sequential_task(self):
        # Step 1: User 1 - Account Creation
        payload_user1 = {
            "username": "testuser1",
            "password": "testpassword",
            "email": "testuser1@example.com"
        }
        response = self.client.post("/authentication/account", json=payload_user1)
        if response.status_code == 201:
            print("Step 1: User 1 - Account Creation successful")
 
        # Step 2: User 2 - Account Creation
        payload_user2 = {
            "username": "testuser2",
            "password": "testpassword",
            "email": "testuser2@example.com"
        }
        response = self.client.post("/authentication/account", json=payload_user2)
        if response.status_code == 201:
            print("Step 2: User 2 - Account Creation successful")
 
        # Step 3: User 3 - Account Creation
        payload_user3 = {
            "username": "testuser3",
            "password": "testpassword",
            "email": "testuser3@example.com"
        }
        response = self.client.post("/authentication/account", json=payload_user3)
        if response.status_code == 201:
            print("Step 3: User 3 - Account Creation successful")
 
 
        # Step 5: User 1 - LogIn
        payload_user1_login = {"username": "testuser1", "password": "testpassword"}
        response = self.client.post("/authentication/auth", json=payload_user1_login)
        if response.status_code == 200:
            token_user1 = response.json().get("token")
            print("Step 5: User 1 - LogIn successful")
        else:
            return
 
        # Step 6: User 2 - LogIn
        payload_user2_login = {"username": "testuser2", "password": "testpassword"}
        response = self.client.post("/authentication/auth", json=payload_user2_login)
        if response.status_code == 200:
            token_user2 = response.json().get("token")
            print("Step 6: User 2 - LogIn successful")
        else:
            return
 
        # Step 7: User 3 - LogIn
        payload_user3_login = {"username": "testuser3", "password": "testpassword"}
        response = self.client.post("/authentication/auth", json=payload_user3_login)
        if response.status_code == 200:
            token_user3 = response.json().get("token")
            print("Step 7: User 3 - LogIn successful")
        else:
            return
 
 
        # Step 10: User 1 - Update Account
        headers_user1 = {"x-access-token": token_user1}
        payload_update_user1 = {
            "username": "iacopo1",
            "email": "iacopo1@gmail.com",
            "password": "password1"
        }
        response = self.client.patch(
            "/authentication/account?accountId=1",
            json=payload_update_user1,
            headers=headers_user1
        )
        if response.status_code == 200:
            print("Step 10: User 1 - Update Account successful")
        else:
            return
 
        # Step 11: User 1 - Get UserId after changes
        response = self.client.get("/authentication/userId?username=iacopo1", headers=headers_user1)
        if response.status_code == 200:
            print("Step 11: User 1 - Get UserId after changes successful")
        else:
            return
 
        # Step 12: User 1 - Get User Info
        response = self.client.get("/authentication/players/1", headers=headers_user1)
        if response.status_code == 200:
            print("Step 12: User 1 - Get User Info successful")
 
        # Step 13: User 1 - Buy Currency
        response = self.client.post("/market_service/players/1/currency/buy?amount=500", headers=headers_user1)
        if response.status_code == 200:
            print("Step 13: User 1 - Buy Currency successful")
 
        # Step 14: User 2 - Buy Currency
        headers_user2 = {"x-access-token": token_user2}
        response = self.client.post("/market_service/players/2/currency/buy?amount=500", headers=headers_user2)
        if response.status_code == 200:
            print("Step 14: User 2 - Buy Currency successful")
 
        # Step 15: User 3 - Buy Currency
        headers_user3 = {"x-access-token": token_user3}
        response = self.client.post("/market_service/players/3/currency/buy?amount=500", headers=headers_user3)
        if response.status_code == 200:
            print("Step 15: User 3 - Buy Currency successful")
 
        # Step 16: User 1 - Get User Transaction
        response = self.client.get("/market_service/players/1/transactions", headers=headers_user1)
        if response.status_code == 200:
            print("Step 16: User 1 - Get User Transaction successful")
 
        # Step 17: User 1 - See Catalogue
        response = self.client.get("/market_service/catalog", headers=headers_user1)
        if response.status_code == 200:
            print("Step 17: User 1 - See Catalogue successful")
 
        # Step 18: User 1 - Makes a Gacha Roll
        response = self.client.post("/market_service/players/1/gacha/roll", headers=headers_user1)
        if response.status_code == 200:
            gacha_id = response.json().get("pilot").get("id")
            print("Step 18: User 1 - Makes a Gacha Roll successful")
        else:
            return
 
        # Step 19: User 1 - Sets up a new Auction
        payload_auction = {"gacha_id": gacha_id, "base_price": 200.0}
        response = self.client.post(
            "/auction_service/players/1/setAuction",
            json=payload_auction,
            headers=headers_user1
        )
        if response.status_code == 201:
            auction_id = response.json().get("auction_id")
            print("Step 19: User 1 - Sets up a new Auction successful")
        else:
            return
 
        # Step 20: User 1 - See Active Auctions
        response = self.client.get("/auction_service/auctions/active", headers=headers_user1)
        if response.status_code == 200:
            print("Step 20: User 1 - See Active Auctions successful")
 
        # Step 21: User 2 - Bid
        payload_bid_user2 = {"user_id": 2, "bid_amount": 300.0}
        response = self.client.post(
            f"/auction_service/auctions/{auction_id}/bid",
            json=payload_bid_user2,
            headers=headers_user2
        )
        if response.status_code == 200:
            print("Step 21: User 2 - Bid successful")
        else:
            return
 
        # Step 22: User 3 - Bid
        payload_bid_user3 = {"user_id": 3, "bid_amount": 500.0}
        response = self.client.post(
            f"/auction_service/auctions/{auction_id}/bid",
            json=payload_bid_user3,
            headers=headers_user3
        )
        if response.status_code == 200:
            print("Step 22: User 3 - Bid successful")
        else:
            return
       # Step 23: User 1 - Checks Wallet after Auction
        response = self.client.get("/authentication/players/1", headers=headers_user1)
        if response.status_code == 200:
            wallet_balance = response.json().get("wallet")
            if wallet_balance == 900:
                print("Step 23: User 1 - Wallet balance is correct after auction")
            else:
                print("Step 23: User 1 - Wallet balance is incorrect")
 
        # Step 24: User 2 - Checks Wallet after Auction
        response = self.client.get("/authentication/players/2", headers=headers_user2)
        if response.status_code == 200:
            wallet_balance = response.json().get("wallet")
            if wallet_balance == 500:
                print("Step 24: User 2 - Wallet balance is correct after auction")
            else:
                print("Step 24: User 2 - Wallet balance is incorrect")
 
        # Step 25: User 3 - Checks Wallet after Auction
        response = self.client.get("/authentication/players/3", headers=headers_user3)
        if response.status_code == 200:
            wallet_balance = response.json().get("wallet")
            if wallet_balance == 0:
                print("Step 25: User 3 - Wallet balance is correct after auction")
            else:
                print("Step 25: User 3 - Wallet balance is incorrect")
 
        # Step 26: User 1 - Get User Gachas
        response = self.client.get(f"/gacha_service/players/1/gachas/{gacha_id}", headers=headers_user1)
        if response.status_code == 200:
            print("Step 26: User 1 - Get User Gachas successful")
 
        # Step 27: User 1 - Get User Missing Gachas
        response = self.client.get("/gacha_service/players/1/gachas/missing", headers=headers_user1)
        if response.status_code == 200:
            print("Step 27: User 1 - Get User Missing Gachas successful")
 
        # Step 28: User 3 - Get a Won Gacha Info
        response = self.client.get(f"/gacha_service/players/3/gachas/{gacha_id}", headers=headers_user3)
        if response.status_code == 200:
            print("Step 28: User 3 - Get a Won Gacha Info successful")
 
 
        # Step 30: User 1 - Logout
        response = self.client.patch("/authentication/logout?accountId=1", headers=headers_user1)
        if response.status_code == 200:
            print("Step 30: User 1 - Logout successful")
 
 
        # Step 32: User 1 - LogIn (Updated Credentials)
        payload_user1_login_updated = {"username": "iacopo1", "password": "password1"}
        response = self.client.post("/authentication/auth", json=payload_user1_login_updated)
        if response.status_code == 200:
            token_user1 = response.json().get("token")
            print("Step 32: User 1 - LogIn with updated credentials successful")
        else:
            return
 
        # Step 33: User 1 - Delete Account
        response = self.client.delete("/authentication/account?accountId=1", headers=headers_user1)
        if response.status_code == 200:
            print("Step 33: User 1 - Delete Account successful")
 
        # Step 34: User 2 - Delete Account
        response = self.client.delete("/authentication/account?accountId=2", headers=headers_user2)
        if response.status_code == 200:
            print("Step 34: User 2 - Delete Account successful")
 
        # Step 35: User 3 - Delete Account
        response = self.client.delete("/authentication/account?accountId=3", headers=headers_user3)
        if response.status_code == 200:
            print("Step 35: User 3 - Delete Account successful")
