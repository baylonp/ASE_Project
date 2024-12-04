## Table of Content

- [Partecipants]()
- [Gachas Overview]()
- [Architecture](https://github.com/baylonp/ASE_Project/blob/test/docs/REPORT.md#architecture)
- [User Stories](https://github.com/baylonp/ASE_Project/blob/test/docs/REPORT.md#user-stories)
- [Market Rules]()




# Architecture

- authentication service: let user create account, login, logout. Has endoints to update the balance of users and to get user ifnormation suche as ID
- Gacha Service: Lets the user see information about his gacha collection, add a gacha to his collection, retrieve the list of missing gatchas. Has also an endpoint that gets called by the auction_service to update the new ownership of the gatcha won during the auction. An admin is also able to call an endpoint inside this service to update some gacha information(for all users).
- Gacha Market Servuce: The user can see its transactions history,can buy in-game currency, purchase a roll and see the whole list of available gachas.
- Auction Service: Lets a user see the active auctions, create an auction and place a bid on an active auction
- Admin Service: Lets the admin authenticate, logout and manage user gacha collections.
- User Nginx Gateway: public endpoint connection for user actions.
- Admin Nginx Gateway: endpoint fot admin connection and operations

| Microservice  | Connections | Details |
| ------------- | ------------- |------------- |
|Authentication service  | To Gacha_service to delite user gacha collection when the account is deleted  | Flask , Python  | 
| Gacha Service  | to Gacha_Market_Service to retrieve the whole gacha catalogue. To Admin_Service to verify that the request made to sprea th emodofication to a gacha to other users is made by an actual admin | Flask, Python  | 
| Gacha Market Service  | To Auth_service to update the currency when an user bought in -game currency and also to see if the user_id is actually a user. To the Gacha_service in order to add a gacha to a user collection and finally to the Admin_Service to verify it is an actual admin that wants to mody gacha info ONLY in the catalogue| Flask, Python | 
| Auction Service  | To Gacha_Service to check if th euser actually owns the gacha he is trying to sell and to update the ownership of that gacha when the auction has ended. To the Authentication_Service to check if the user has enough in game currency before bidding, to update the currency when an auction is not won and also when it is won( subtracting money or giving the user money back)   | Flask, Python  | 
| Admin_Service  | To Gacha_Market_Service to update gacha info in the catalogue. To the Authentication Service to obtain info about a user. To the Gacha_Service to spread the modification made to a gacha to all users owning that gacha  | Flask, Python | 
| User_Nginx_Gateway  | to all the services  | Nginx | 
| Admin_Nginx_Gatway | to admin_Service  | Nginx | t

## User Stories

- **4. create my game account/profile**
- **5. delete my game account/profile**
- **6. modify my account/profile**
- **7. login and logout from the system**
- 8. be safe about my account/profile data
- **9. see my gacha collection**
- **10. want to see the info of a gacha of my collection**
- **11. see the system gacha collection**
- **12. want to see the info of a system gacha**
- **13. use in-game currency to roll a gacha**
- **14. buy in-game currency**
- 15. be safe about the in-game currency transactions
- **16. see the auction market**
- **17. set an auction for one of my gacha**
- **18. bid for a gacha from the market**
- **19. view my transaction history**
- **20. receive a gacha when I win an auction**
- **21. receive in-game currency when someone win my auction**
- **22. receive my in-game currency back when I lost an auction**
- 23. that the auctions cannot be tampered


**Paths**


- 4 --> [POST] localhost/authentication/account (User_gateway, AUthentication_Service, UsersDB)
- 5 --> [DELETE] localhost/authentication/account (User_gateway, AUthentication_Service, UsersDB)
- 6 --> [PATCH] localhost/authentication/account (User_gateway, AUthentication_Service, UsersDB)
- 7 --> [POST] localhost/authentication/auth  //   [PATCH] localhost/authentication/logout  (User_gateway, AUthentication_Service, UsersDB)
- 8 -->
- 9 --> [GET] localhost//gacha_service/players/<userID>/gachas  (User_gateway, gacha_service, issuedANDownedDB)
- 10 --> [GET] localhost/gacha_service/players/<userID>/gachas/<gachaId> (User_gateway, gacha_service, issuedANDownedDB)
- 11 --> [GET] localhost/market_service/catalog (user_gateway, gacha_market_service)
- 12 --> [GET] localhost/gacha_service/players/<userID>/gachas/missing (User_gateway, gacha_service, gacha_market_service)
- 13 --> [POST] localhost/market_service/players/<playerId>/gacha/roll   (User_gateway, gacha_market_service, AUthentication_Service, gacha_service)
- 14 --> [POST] localhost/market_service/players/<playerId>/currency/buy (User_gateway, gacha_market_service, AUthentication_Service)
- 15 -->
- 16 --> [GET] localhost/auction_service/auctions/active (User_gateway, auction_service, auctions.db)
- 17 --> [POST] localhost/auction_service/players/<userId>/setAuction (User_gateway, AUthentication_Service, auction_service, auctions.db) 
- 18 -->  [POST] localhost/auction_service/auctions/<auctionID>/bid  (User_gateway, AUthentication_Service,auction_service, AUthentication_Service, auctions.db) 
- 19 --> [GET] localhost/market_service/players/<userId>/transactions  (User_gateway, AUthentication_Service,gacha_market_service, gacha_market.db)
- 20 -->  [PATCH] localhost/gacha_service/players/{auction.current_user_winner_id}/gachas/{auction.gacha_id}/update_owner (auction_service, gacha_service )
- 21 --> [PATCH] localhost/authentication/players/{auction.issuer_id}/currency/update  (auction_service, authentication_service)
- 22 --> [PATCH] localhost/authentication/players/{user_id}/currency/update (auction_service, authentication_service)
- 23 -->

## Market Rules

Whenever the user wants to auction off a gacha the he owns, he sets the base price and the auction appears to all the users. Whenever a users places a bid higher than the previus one, the previous bidder receives the money back and is able to bid again if he wants. Bids are placeable for the whole duration of the auction. The moment a user bids, funds are withdrawn from his balance. He will receive the funds back only in the moment a higher bid is placed. The highest bidder at the end of the time wins the auction and receives the gacha auctioned off by the original issuer.

In the eventuality the winning bidder places a even higher bid, there is no control put in place, on purpose, and only the last bid is taken into consideration.




## Testing
# In Isolation
# performance(locust)
# integration(jacopo)
