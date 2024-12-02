from locust import HttpUser, task, between
import json
import string
import random, time
 
class F1DriversGachaUser(HttpUser):
    wait_time = between(1, 1)  # Nessun tempo casuale tra richieste
    
    def on_start(self):
        # This method is called when the virtual user starts
        self.jwt_token1 = None
        self.userId1 = None
        self.jwt_token2 = None
        self.userId2 = None
        self.jwt_token3 = None
        self.userId3 = None
        
        # Disable SSL Verification
        self.client.verify = False
 
    @task
    def sequential_task(self):
        # Step 1: User 1 - Account Creation
        usernameUser1 = ''.join(random.choices(string.ascii_lowercase, k=8))
        passwordUser1 = "0123456789"
        emailUser1 = f"{usernameUser1}@example.com"
        usernameUser2 = ''.join(random.choices(string.ascii_lowercase, k=8))
        passwordUser2 = "9876543210"
        emailUser2 = f"{usernameUser2}@example.com"
        usernameUser3 = ''.join(random.choices(string.ascii_lowercase, k=8))
        passwordUser3 = "6547891230"
        emailUser3 = f"{usernameUser3}@example.com"

        payload_user1 = {
            "username": usernameUser1,
            "password": passwordUser1,
            "email": emailUser1
        }
        response = self.client.post("/authentication/account", json=payload_user1)
        if response.status_code == 201:
            print("Step 1: User 1 - Account Creation successful")
        else:
            return
 
        # Step 2: User 2 - Account Creation
        payload_user2 = {
            "username": usernameUser2,
            "password": passwordUser2,
            "email": emailUser2
        }
        response = self.client.post("/authentication/account", json=payload_user2)
        if response.status_code == 201:
            print("Step 2: User 2 - Account Creation successful")
        else:
            return
 
        # Step 3: User 3 - Account Creation
        payload_user3 = {
            "username": usernameUser3,
            "password": passwordUser3,
            "email": emailUser3
        }
        response = self.client.post("/authentication/account", json=payload_user3)
        if response.status_code == 201:
            print("Step 3: User 3 - Account Creation successful")
        else:
            return
 
 
        # Step 5: User 1 - LogIn
        payload_user1_login = {"username": usernameUser1, "password": passwordUser1}
        response = self.client.post("/authentication/auth", json=payload_user1_login)
        if response.status_code == 200:
            self.jwt_token1 = response.json().get("token")
            self.userId1 = response.json().get("userId")
            print("Step 5: User 1 - LogIn successful")
        else:
            return
 
        # Step 6: User 2 - LogIn
        payload_user2_login = {"username": usernameUser2, "password": passwordUser2}
        response = self.client.post("/authentication/auth", json=payload_user2_login)
        if response.status_code == 200:
            self.jwt_token2 = response.json().get("token")
            self.userId2 = response.json().get("userId")
            print("Step 6: User 2 - LogIn successful")
        else:
            return
 
        # Step 7: User 3 - LogIn
        payload_user3_login = {"username": usernameUser3, "password": passwordUser3}
        response = self.client.post("/authentication/auth", json=payload_user3_login)
        if response.status_code == 200:
            self.jwt_token3 = response.json().get("token")
            self.userId3 = response.json().get("userId")
            print("Step 7: User 3 - LogIn successful")
        else:
            print(f"Step 7: User 3 - LogIn unsuccsesful - {response.status_code}")
            return
 

        # Step 10: User 1 - Update Account
        usernameUser1Updated = ''.join(random.choices(string.ascii_lowercase, k=8))
        passwordUser1Updated = "CAPOsonoSTANCO"
        emailUser1Updated = f"{usernameUser1Updated}@example.com"
        
        headers_user1 = {"x-access-token": self.jwt_token1}
        payload_update_user1 = {
            "username": usernameUser1Updated,
            "email": emailUser1Updated,
            "password": passwordUser1Updated
        }
        
        response = self.client.patch(
            f"/authentication/account",
            json=payload_update_user1,
            params={"accountId": self.userId1},
            headers=headers_user1
        )
        if response.status_code == 200:
            print("Step 10: User 1 - Update Account successful")
        else:
            print(f"Step 10: User 1 - Update unsuccsesful - {response.status_code}")
            return
 
        # Step 11: User 1 - Get UserId after changes
        response = self.client.get(f"/authentication/userId", params={"username": usernameUser1Updated},  headers=headers_user1)
        if response.status_code == 200:
            print("Step 11: User 1 - Get UserId after changes successful")
        else:
            return
 
        # Step 12: User 1 - Get User Info
        response = self.client.get(f"/authentication/players/{self.userId1}", headers=headers_user1)
        if response.status_code == 200:
            print("Step 12: User 1 - Get User Info successful")
        else:
            return
 
        # Step 13: User 1 - Buy Currency
        response = self.client.post(f"/market_service/players/{self.userId1}/currency/buy?amount=500", headers=headers_user1)
        if response.status_code == 200:
            print("Step 13: User 1 - Buy Currency successful")
        else:
            return
 
        # Step 14: User 2 - Buy Currency
        headers_user2 = {"x-access-token": self.jwt_token2}
        response = self.client.post(f"/market_service/players/{self.userId2}/currency/buy?amount=500", headers=headers_user2)
        if response.status_code == 200:
            print("Step 14: User 2 - Buy Currency successful")
        else:
            return
 
        # Step 15: User 3 - Buy Currency
        headers_user3 = {"x-access-token": self.jwt_token3}
        response = self.client.post(f"/market_service/players/{self.userId3}/currency/buy?amount=500", headers=headers_user3)
        if response.status_code == 200:
            print("Step 15: User 3 - Buy Currency successful")
        else:
            return
 
        # Step 16: User 1 - Get User Transaction
        response = self.client.get(f"/market_service/players/{self.userId1}/transactions", headers=headers_user1)
        if response.status_code == 200:
            print("Step 16: User 1 - Get User Transaction successful")
        else:
            return
 
        # Step 17: User 1 - See Catalogue
        response = self.client.get("/market_service/catalog", headers=headers_user1)
        if response.status_code == 200:
            print("Step 17: User 1 - See Catalogue successful")
        else:
            return
 
        # Step 18: User 1 - Makes a Gacha Roll
        gacha_id = None
        response = self.client.post(f"/market_service/players/{self.userId1}/gacha/roll", headers=headers_user1)
        if response.status_code == 200:
            gacha_id = response.json().get("pilot").get("id")
            print("Step 18: User 1 - Makes a Gacha Roll successful")
        else:
            return
 
        # Step 19: User 1 - Sets up a new Auction
        auction_id = None
        payload_auction = {"gacha_id": gacha_id, "base_price": 200.0}
        response = self.client.post(
            f"/auction_service/players/{self.userId1}/setAuction",
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
        else:
            return
 
        # Step 21: User 2 - Bid
        payload_bid_user2 = {"user_id": self.userId2, "bid_amount": 300.0}
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
        payload_bid_user3 = {"user_id": self.userId3, "bid_amount": 500.0}
        response = self.client.post(
            f"/auction_service/auctions/{auction_id}/bid",
            json=payload_bid_user3,
            headers=headers_user3
        )
        if response.status_code == 200:
            print("Step 22: User 3 - Bid successful")
        else:
            return
        
        time.sleep(11)
        
        # Step 23: User 1 - Checks Wallet after Auction
        wallet_balance = None
        response = self.client.get(f"/authentication/players/{self.userId1}", headers=headers_user1)
        if response.status_code == 200:
            wallet_balance = response.json().get("wallet")
            if wallet_balance == 900:
                print("Step 23: User 1 - Wallet balance is correct after auction")
            else:
                print("Step 23: User 1 - Wallet balance is incorrect")
        else:
            return
 
        # Step 24: User 2 - Checks Wallet after Auction
        response = self.client.get(f"/authentication/players/{self.userId2}", headers=headers_user2)
        if response.status_code == 200:
            wallet_balance = response.json().get("wallet")
            if wallet_balance == 500:
                print("Step 24: User 2 - Wallet balance is correct after auction")
            else:
                print("Step 24: User 2 - Wallet balance is incorrect")
        else:
            return
 
        # Step 25: User 3 - Checks Wallet after Auction
        response = self.client.get(f"/authentication/players/{self.userId3}", headers=headers_user3)
        if response.status_code == 200:
            wallet_balance = response.json().get("wallet")
            if wallet_balance == 0:
                print("Step 25: User 3 - Wallet balance is correct after auction")
            else:
                print("Step 25: User 3 - Wallet balance is incorrect")
        else:
            return
 
        # Step 26: User 1 - Get User Gachas
        response = self.client.get(f"/gacha_service/players/{self.userId1}/gachas", headers=headers_user1)
        if response.status_code == 200:
            print("Step 26: User 1 - Get User Gachas successful")
        else:
            return
 
        # Step 27: User 1 - Get User Missing Gachas
        response = self.client.get(f"/gacha_service/players/{self.userId1}/gachas/missing", headers=headers_user1)
        if response.status_code == 200:
            print("Step 27: User 1 - Get User Missing Gachas successful")
        else:
            return
 
        # Step 28: User 3 - Get a Won Gacha Info
        response = self.client.get(f"/gacha_service/players/{self.userId3}/gachas/{gacha_id}", headers=headers_user3)
        if response.status_code == 200:
            print("Step 28: User 3 - Get a Won Gacha Info successful")
        else:
            return
 
        # Step 30: User 1 - Logout
        response = self.client.patch(f"/authentication/logout", params={"accountId": self.userId1}, headers=headers_user1)
        if response.status_code == 200:
            print("Step 30: User 1 - Logout successful")
        else:
            return
 
        # Step 32: User 1 - LogIn (Updated Credentials)
        payload_user1_login_updated = {"username": usernameUser1Updated, "password": passwordUser1Updated}
        response = self.client.post("/authentication/auth", json=payload_user1_login_updated)
        if response.status_code == 200:
            self.jwt_token1 = response.json().get("token")
            print("Step 32: User 1 - LogIn with updated credentials successful")
        else:
            return
 
        # Step 33: User 1 - Delete Account
        headers_user1_upd = {"x-access-token": self.jwt_token1}
        response = self.client.delete(f"/authentication/account", params={"accountId": self.userId1}, headers=headers_user1_upd)
        if response.status_code == 200:
            print("Step 33: User 1 - Delete Account successful")
        else:
            return
        
        # Step 34: User 2 - Delete Account
        response = self.client.delete(f"/authentication/account", params={"accountId": self.userId2}, headers=headers_user2)
        if response.status_code == 200:
            print("Step 34: User 2 - Delete Account successful")
        else:
            return
        
        # Step 35: User 3 - Delete Account
        response = self.client.delete(f"/authentication/account", params={"accountId": self.userId3}, headers=headers_user3)
        if response.status_code == 200:
            print("Step 35: User 3 - Delete Account successful")
        else:
            return
