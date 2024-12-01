from flask import Flask, request, jsonify, make_response
from datetime import datetime, timedelta
from functools import wraps
import threading
import random

app = Flask(__name__)

# Configurazione simulata
app.config['SECRET_KEY'] = 'your_secret_key'

# Mock del database delle aste
MOCK_AUCTIONS = []
MOCK_USERS = {"1": {"wallet": 500}, "2": {"wallet": 300}}
MOCK_GACHAS = [{"gacha_id": 101, "owner_id": 1}, {"gacha_id": 102, "owner_id": 2}]
AUCTION_ID_COUNTER = 1

# Simulazione token
USER_TOKEN = "jwt_token_example"


# Decoratore mock per autenticazione
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token or token != USER_TOKEN:
            return jsonify({'message': 'Token is invalid or missing!'}), 401
        current_user = 1  # Utente mock con ID 1
        return f(current_user, token, *args, **kwargs)
    return decorated


# Endpoint per creare un'asta
@app.route('/auction_service/players/<userId>/setAuction', methods=['POST'])
@token_required
def set_auction(current_user, token, userId):
    # Verifica token
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    if token != USER_TOKEN:
        return jsonify({'message': 'Unauthorized access'}), 403

    if str(current_user) != userId:
        return jsonify({'message': 'Unauthorized action!'}), 403  # Verifica che l'utente sia autorizzato

    try:
        # Recupera i dati dall'input JSON
        data = request.json
        if not data or 'gacha_id' not in data or 'base_price' not in data:
            return make_response(jsonify({'message': 'Invalid input data'}), 400)

        gacha_id = data['gacha_id']
        base_price = data['base_price']

        # Simula la verifica della proprietà del gacha
        gacha = next((g for g in MOCK_GACHAS if g['gacha_id'] == gacha_id and g['owner_id'] == int(userId)), None)
        if not gacha:
            return jsonify({'message': 'Gacha not found or not owned by user'}), 404

        # Creazione di una nuova asta
        global AUCTION_ID_COUNTER
        new_auction = {
            'auction_id': AUCTION_ID_COUNTER,
            'gacha_id': gacha_id,
            'issuer_id': int(userId),
            'current_user_winner_id': int(userId),
            'current_bid': base_price,
            'is_active': True,
            'start_time': datetime.now().isoformat()
        }
        MOCK_AUCTIONS.append(new_auction)
        AUCTION_ID_COUNTER += 1

        # Timer per terminare l'asta
        threading.Timer(10.0, end_auction, args=(new_auction['auction_id'],)).start()

        return jsonify({'message': 'Auction created successfully', 'auction_id': new_auction['auction_id']}), 201

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)


# Endpoint per ottenere tutte le aste attive
@app.route('/auction_service/auctions/active', methods=['GET'])
def get_active_auctions():
    try:
        # Simula la query per trovare tutte le aste attive
        active_auctions = [auction for auction in MOCK_AUCTIONS if auction['is_active']]

        if not active_auctions:
            return make_response(jsonify({'message': 'No active auctions found'}), 404)

        # Preparare la lista dei risultati
        result = []
        for auction in active_auctions:
            result.append({
                'auction_id': auction['auction_id'],
                'gacha_id': auction['gacha_id'],
                'issuer_id': auction['issuer_id'],
                'current_user_winner_id': auction['current_user_winner_id'],
                'current_bid': auction['current_bid'],
                'start_time': auction['start_time']  # Il timestamp è già formattato come stringa
            })

        return make_response(jsonify(result), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)



@app.route('/auction_service/auctions/<auctionID>/bid', methods=['POST'])
@token_required
def place_bid(current_user, token, auctionID):
     # Verifica token
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    if token != USER_TOKEN:
        return jsonify({'message': 'Unauthorized access'}), 403

    try:
        
        # Ottieni i dati dall'input JSON
        data = request.json
        if not data or 'bid_amount' not in data:
            return make_response(jsonify({'message': 'Invalid input data'}), 400)

        bid_amount = data['bid_amount']

        # Recupera l'asta dal mock database
        auction = next((a for a in MOCK_AUCTIONS if a['auction_id'] == int(auctionID)), None)
        if not auction:
            return jsonify({'message': 'Auction not found'}), 404

        # Verifica se l'asta è attiva
        if not auction['is_active']:
            return jsonify({'message': 'Auction is no longer active'}), 400

        # Recupera il wallet dell'utente corrente dal mock database
        user_wallet = MOCK_USERS.get(str(current_user), {}).get('wallet', 0)
        if user_wallet < bid_amount:
            return jsonify({'message': 'Insufficient funds'}), 400

        # Verifica che la puntata sia maggiore dell'attuale
        if bid_amount <= auction['current_bid']:
            return jsonify({'message': 'Bid amount must be higher than the current bid'}), 400

        # Restituisce i fondi al precedente vincitore (se applicabile)
        previous_winner_id = auction['current_user_winner_id']
        if previous_winner_id and previous_winner_id != auction['issuer_id']:
            MOCK_USERS[str(previous_winner_id)]['wallet'] += auction['current_bid']

        # Aggiorna l'asta con il nuovo vincitore e la nuova puntata
        MOCK_USERS[str(current_user)]['wallet'] -= bid_amount
        auction['current_user_winner_id'] = current_user
        auction['current_bid'] = bid_amount

        return jsonify({'message': 'Bid placed successfully'}), 200

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)



# Funzione per terminare l'asta simulata
def end_auction(auction_id):
    auction = next((a for a in MOCK_AUCTIONS if a['auction_id'] == auction_id), None)
    if auction and auction['is_active']:
        auction['is_active'] = False

        # Trasferisci i fondi all'emittente se il vincitore è diverso
        winner_id = auction['current_user_winner_id']
        if winner_id != auction['issuer_id']:
            MOCK_USERS[str(auction['issuer_id'])]['wallet'] += auction['current_bid']

        # Trasferisci il gacha al vincitore
        gacha = next((g for g in MOCK_GACHAS if g['gacha_id'] == auction['gacha_id']), None)
        if gacha:
            gacha['owner_id'] = winner_id



if __name__ == '__main__':
    app.run(debug=True)
