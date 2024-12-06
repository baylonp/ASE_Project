import threading
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
import requests
import jwt
from functools import wraps
from requests.exceptions import Timeout, RequestException
import re
import os

app = Flask(__name__)
 
# Configurazione del database per le aste
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/auctions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable not set!")
app.config['SECRET_KEY'] = secret_key
 
db = SQLAlchemy(app)
 
# Definizione del modello Auction
class Auction(db.Model):
    tablename = 'auctions'
    auction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gacha_id = db.Column(db.Integer, nullable=False)
    issuer_id = db.Column(db.Integer, nullable=False)
    current_user_winner_id = db.Column(db.Integer, nullable=True, default=None)
    current_bid = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
 
    def repr(self):
        return f'<Auction {self.auction_id}, Gacha {self.gacha_id}, Issuer {self.issuer_id}>'
 
# Creazione del database
with app.app_context():
    db.create_all()
 
GACHA_SERVICE_URL = 'https://gacha_service:5000'
AUTH_SERVICE_URL = 'https://authentication_service:5000'
 
# Decoratore per proteggere gli endpoint con autenticazione JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')  # Il token deve essere inviato nell'header della richiesta
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Decode HTTP Received Token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Verifica se è un token utente o admin
            if 'user_id' in data:
                # send a request to the auth service to verify the token.
                # Logica per token user
                username = data['username']
                id = data['user_id']
                
                
                # Effettua una richiesta HTTP al servizio esterno
                user_service_url = "https://authentication_service:5000/authentication/validate"
                payload = {'user_username': username}
                try:
                    response = requests.get(user_service_url, headers={'x-access-token': token}, verify=False,timeout=5)
                    # Ensure status code is 200
                    if response.status_code != 200:
                        return jsonify(response.json()), 403
                    
                    if 'application/json' not in response.headers.get('Content-Type', ''):
                        return jsonify({'message': 'Invalid response format from admin service!', 'details': response.text}), 500
                    
                    # Parse the JSON body
                    user_data = {
                        'username': username,
                        'user_id': id
                    }
                    
                    return f(user_data, token, *args, **kwargs)
                except Timeout:
                    # If the request times out, return an appropriate message
                    return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable
                except requests.exceptions.RequestException as e:
                    # Gestisci errori durante la richiesta HTTP
                    return jsonify({'message': 'Error validating admin token!', 'error': str(e)}), 500
            
            elif 'admin_id' in data:
                # send a request to the admin service to verify the token.
                # Logica per token admin
                username = data['username']
                
                # Effettua una richiesta HTTP al servizio esterno
                admin_service_url = "https://admin_service:5000/admin_service/verify_admin"
                payload = {'admin_username': username}
                try:
                    response = requests.get(admin_service_url, headers={'x-access-token': token}, verify=False, timeout=5)
                    # Ensure status code is 200
                    if response.status_code != 200:
                        return jsonify(response.json()), 403
                    
                    if 'application/json' not in response.headers.get('Content-Type', ''):
                        return jsonify({'message': 'Invalid response format from admin service!', 'details': response.text}), 500
                    
                    # Parse the JSON body
                    admin_data = {
                        'username': username
                    }
                    
                    return f(admin_data, token, *args, **kwargs)
                
                except Timeout:
                    # If the request times out, return an appropriate message
                    return make_response(jsonify({'message': 'Admin service is temporarily unavailable'}), 503)  # Service Unavailable
                
                except requests.exceptions.RequestException as e:
                    # Gestisci errori durante la richiesta HTTP
                    return jsonify({'message': 'Error validating admin token!', 'error': str(e)}), 500
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
    return decorated
 
@app.route('/auction_service/players/<userId>/setAuction', methods=['POST'])
@token_required
def set_auction(current_user, token, userId):
    """
    Permette a un utente di mettere all'asta uno dei suoi gacha, assicurandosi che non superi il numero posseduto
    """
        
    if not re.match(r'^\d+$', str(userId)):
        return make_response(jsonify({'message': 'Invalid user ID, must be a positive number'}), 400)
    
    try:
        # Recuperare i dati dall'input JSON
        data = request.json
        if not data or 'gacha_id' not in data or 'base_price' not in data:
            return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
        gacha_id = data['gacha_id']
        base_price = data['base_price']

        if not re.match(r'^\d+$', str(gacha_id)):
            return make_response(jsonify({'message': 'Invalid gacha_id, must be a positive number'}), 400)

        # Effettuare una richiesta al gacha_service per ottenere tutti i gacha posseduti dall'utente
        headers = {'x-access-token': token}
        owned_gachas = None
        try:
            response = requests.get(f"{GACHA_SERVICE_URL}/gacha_service/players/{userId}/gachas", headers=headers, verify=False, timeout=5)
            if response.status_code == 204:  # Nessun gacha trovato
                return make_response(jsonify({'message': 'User does not own any Gachas'}), 400)
            elif response.status_code != 200:
                return make_response(jsonify({'message': 'Error communicating with gacha_service'}), 500)

            owned_gachas = response.json()  # Lista di gachas dell'utente
        except Timeout:
            return make_response(jsonify({'message': 'Gacha service is temporarily unavailable'}), 503)

        # Filtrare i gacha posseduti con l'ID corrispondente
        user_gacha_count = sum(1 for g in owned_gachas if g['gachaId'] == gacha_id)
        if user_gacha_count == 0:
            return make_response(jsonify({'message': 'User does not own this Gacha'}), 400)

        # Controllare le aste attive per vedere quanti gacha sono già in asta
        active_auctions = Auction.query.filter_by(issuer_id=userId, gacha_id=gacha_id, is_active=True).count()

        # Calcolare il numero disponibile di questo tipo di gacha
        available_gachas = user_gacha_count - active_auctions
        if available_gachas <= 0:
            return make_response(jsonify({'message': 'All of your Gachas of this type are already in auction'}), 400)

        # Creare una nuova asta nel database
        new_auction = Auction(
            gacha_id=gacha_id,
            issuer_id=userId,
            current_user_winner_id=userId,
            current_bid=base_price,
            is_active=True,
            start_time=datetime.now(timezone.utc)  # Timestamp in UTC
        )
 
        db.session.add(new_auction)
        db.session.commit()

        # Attivare un timer per disattivare l'asta dopo 1 minuto, passando il token come argomento
        auction_id = new_auction.auction_id
        timer = threading.Timer(60.0, end_auction, [auction_id, token])
        timer.start()

        return make_response(jsonify({'message': 'Auction created successfully', 'auction_id': auction_id}), 201)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

 
@app.route('/auction_service/auctions/active', methods=['GET'])
def get_active_auctions():
    """
    Restituisce la lista di tutte le aste attive
    ---
    """
    try:
        # Query per trovare tutte le aste attive
        active_auctions = Auction.query.filter_by(is_active=True).all()
        #active_auctions = Auction.query.all()

        if not active_auctions:
            return make_response(jsonify({'message': 'No active auctions found'}), 404)

        # Preparare la lista dei risultati
        result = []
        for auction in active_auctions:
            result.append({
                'auction_id': auction.auction_id,
                'gacha_id': auction.gacha_id,
                'issuer_id': auction.issuer_id,
                'current_user_winner_id': auction.current_user_winner_id,
                'current_bid': auction.current_bid,
                'start_time': auction.start_time.isoformat()  # Convertire il timestamp in un formato leggibile
            })

        return make_response(jsonify(result), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

@app.route('/auction_service/auctions/<auctionID>/bid', methods=['POST'])
@token_required
def place_bid(current_user, token, auctionID):
    """
    Permette a un utente di fare una puntata su un'asta specifica
    """

    # Validazione del parametro auctionID come numero intero
    if not re.match(r'^\d+$', str(auctionID)):
        return make_response(jsonify({'message': 'Invalid auctionID, must be a positive number'}), 400)


    try:
        # Ottenere i dati dall'input JSON
        data = request.json
        if not data or 'bid_amount' not in data or 'user_id' not in data:
            return make_response(jsonify({'message': 'Invalid input data'}), 400)

        user_id = data['user_id']  # Utilizziamo l'ID utente dal token
        bid_amount = data['bid_amount']

        # Validazione del parametro user_id come numero intero
        if not re.match(r'^\d+$', str(user_id)):
            return make_response(jsonify({'message': 'Invalid user_id, must be a positive number'}), 400)

        # Validazione del parametro user_id come numero intero
        if not re.match(r'^\d+(\.\d+)?$', str(bid_amount)):
            return make_response(jsonify({'message': 'Invalid bid_amount, must be a positive number'}), 400)       


        

        # Recuperare l'asta dal database
        auction = Auction.query.get(auctionID)
        if not auction:
            return make_response(jsonify({'message': 'Auction not found'}), 404)

        # Controllare se l'asta è attiva
        if not auction.is_active:
            return make_response(jsonify({'message': 'Auction is no longer active'}), 400)
        
        # Controllare se l'utente è l'emittente dell'asta
        if user_id == auction.issuer_id:
            return make_response(jsonify({'message': 'You cannot bid on your own auction'}), 400)


        try:
            # Verificare che l'utente abbia fondi sufficienti
            headers = {'x-access-token': token}  # Aggiungi il token all'header
            response = requests.get(f"{AUTH_SERVICE_URL}/authentication/players/{user_id}", headers=headers, verify=False, timeout=5)
            
            if response.status_code != 200:
                return make_response(jsonify({'message': 'Failed to retrieve user information from authentication service'}), 500)
        except Timeout:
            # If the request times out, return an appropriate message
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable


        user_data = response.json()
        wallet_balance = user_data.get('wallet', 0)

        if wallet_balance < bid_amount:
            return make_response(jsonify({'message': 'Insufficient funds'}), 400)

        # Controllare se la puntata è superiore all'attuale
        if bid_amount <= auction.current_bid:
            return make_response(jsonify({'message': 'Bid amount must be higher than the current bid'}), 400)

        # Restituire i fondi al precedente vincitore (se esiste e non è l'emittente dell'asta)
        if auction.current_user_winner_id and auction.current_user_winner_id != auction.issuer_id:
            try:
                refund_response = requests.patch(
                    f"{AUTH_SERVICE_URL}/authentication/players/{auction.current_user_winner_id}/currency/update",
                    json={'amount': auction.current_bid},
                    headers=headers,
                    verify=False,
                    timeout=5
                )
                if refund_response.status_code != 200:
                    return make_response(jsonify({'message': 'Failed to refund previous bidder'}), 500)
            except Timeout:
                return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

        try:
            # Decrementare l'importo dal wallet del nuovo offerente
            debit_response = requests.patch(
                f"{AUTH_SERVICE_URL}/authentication/players/{user_id}/currency/update",
                json={'amount': -bid_amount},  # L'importo deve essere sottratto
                headers=headers,
                verify=False,
                timeout=5
            )
            if debit_response.status_code != 200:
                return make_response(jsonify({'message': 'Failed to debit user funds'}), 500)
        
        except Timeout:
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable


        

        # Aggiornare l'asta con il nuovo vincitore e la nuova puntata
        auction.current_user_winner_id = user_id
        auction.current_bid = bid_amount
        db.session.commit()

        return make_response(jsonify({'message': 'Bid placed successfully'}), 200)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with other services: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

def end_auction(auction_id, token):
    """
    Funzione per disattivare l'asta dopo 1 minuto e assegnare il gacha all'utente vincitore
    """
    with app.app_context():
        auction = Auction.query.get(auction_id)
        if auction and auction.is_active:
            auction.is_active = False
            db.session.commit()
 
            headers = {'x-access-token': token}  # Aggiungi il token all'header
 
            # Se il vincitore è diverso dall'emittente, aggiungi i soldi della puntata all'issuer dell'asta
            if auction.current_user_winner_id and auction.current_user_winner_id != auction.issuer_id:
                try:
                    add_funds_response = requests.patch(
                        f"{AUTH_SERVICE_URL}/authentication/players/{auction.issuer_id}/currency/update",
                        json={'amount': auction.current_bid},
                        headers=headers, 
                        verify=False, # Aggiungi il token all'header
                        timeout=5
                    )
                    if add_funds_response.status_code != 200:
                        print(f"Failed to add funds to the issuer {auction.issuer_id} for auction {auction_id}")  

                except Timeout:
                    return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

                    
                if add_funds_response.status_code != 200:
                    print(f"Failed to add funds to the issuer {auction.issuer_id} for auction {auction_id}")
                else:
                    print(f"Funds from the auction successfully added to issuer {auction.issuer_id}")
 
            # Assegnare il gacha all'utente vincitore usando l'endpoint update_owner in gacha_service
            if auction.current_user_winner_id:
                try:
                    update_owner_response = requests.patch(
                        f"{GACHA_SERVICE_URL}/gacha_service/players/{auction.current_user_winner_id}/gachas/{auction.gacha_id}/update_owner",
                        headers=headers,  # Aggiungi il token all'header
                        verify= False,
                        timeout=5
                        
                    )
                except Timeout:
                    return make_response(jsonify({'message': 'Gacha service is temporarily unavailable'}), 503)  # Service unavailable
    
 
 
                if update_owner_response.status_code != 200:
                    print(f"Failed to transfer ownership of gacha {auction.gacha_id} to the winner of auction {auction_id}")
                else:
                    print(f"Gacha {auction.gacha_id} successfully transferred to user {auction.current_user_winner_id}")
 
if __name__ == '__main__':
    app.run()
