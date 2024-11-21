from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
import requests
import threading

app = Flask(__name__)

# Configurazione del database per le aste
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/auctions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

GACHA_SERVICE_URL = 'http://gacha_service:5000'
AUTH_SERVICE_URL = 'http://authentication_service:5000'


@app.route('/auction_service/players/<userId>/setAuction', methods=['POST'])
def set_auction(userId):
    """
    Permette a un utente di mettere all'asta uno dei suoi gacha
    ---
    """
    try:
        # Recuperare i dati dall'input JSON
        data = request.json
        if not data or 'gacha_id' not in data or 'base_price' not in data:
            return make_response(jsonify({'message': 'Invalid input data'}), 400)

        gacha_id = data['gacha_id']
        base_price = data['base_price']

        # Effettuare una richiesta GET al gacha_service per verificare se l'utente possiede il gacha
        response = requests.get(f"{GACHA_SERVICE_URL}/players/{userId}/gachas/{gacha_id}")

        if response.status_code == 404:
            return make_response(jsonify({'message': 'Gacha not found or not owned by user'}), 404)
        elif response.status_code != 200:
            return make_response(jsonify({'message': 'Error communicating with gacha_service'}), 500)

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

        # Attivare un timer per disattivare l'asta dopo 1 minuto
        auction_id = new_auction.auction_id
        timer = threading.Timer(240.0, end_auction, [auction_id])
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
def place_bid(auctionID):
    """
    Permette a un utente di fare una puntata su un'asta specifica
    """
    try:
        # Ottenere i dati dall'input JSON
        data = request.json
        if not data or 'user_id' not in data or 'bid_amount' not in data:
            return make_response(jsonify({'message': 'Invalid input data'}), 400)

        user_id = data['user_id']
        bid_amount = data['bid_amount']

        # Recuperare l'asta dal database
        auction = Auction.query.get(auctionID)
        if not auction:
            return make_response(jsonify({'message': 'Auction not found'}), 404)

        # Controllare se l'asta è attiva
        if not auction.is_active:
            return make_response(jsonify({'message': 'Auction is no longer active'}), 400)

        # Verificare che l'utente abbia fondi sufficienti
        response = requests.get(f"{AUTH_SERVICE_URL}/players/{user_id}")
        if response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to retrieve user information from authentication service'}), 500)

        user_data = response.json()
        wallet_balance = user_data.get('wallet', 0)

        if wallet_balance < bid_amount:
            return make_response(jsonify({'message': 'Insufficient funds'}), 400)

        # Controllare se la puntata è superiore all'attuale
        if bid_amount <= auction.current_bid:
            return make_response(jsonify({'message': 'Bid amount must be higher than the current bid'}), 400)

        # Restituire i fondi al precedente vincitore (se esiste e non è l'emittente dell'asta)
        if auction.current_user_winner_id and auction.current_user_winner_id != auction.issuer_id:
            refund_response = requests.patch(
                f"{AUTH_SERVICE_URL}/players/{auction.current_user_winner_id}/currency/update",
                json={'amount': auction.current_bid}
            )
            if refund_response.status_code != 200:
                return make_response(jsonify({'message': 'Failed to refund previous bidder'}), 500)

        # Decrementare l'importo dal wallet del nuovo offerente
        debit_response = requests.patch(
            f"{AUTH_SERVICE_URL}/players/{user_id}/currency/update",
            json={'amount': -bid_amount}  # L'importo deve essere sottratto
        )
        if debit_response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to debit user funds'}), 500)

        # Aggiornare l'asta con il nuovo vincitore e la nuova puntata
        auction.current_user_winner_id = user_id
        auction.current_bid = bid_amount
        db.session.commit()

        return make_response(jsonify({'message': 'Bid placed successfully'}), 200)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with other services: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
    



def end_auction(auction_id):
    """
    Funzione per disattivare l'asta dopo 1 minuto e assegnare il gacha all'utente vincitore
    """
    with app.app_context():
        auction = Auction.query.get(auction_id)
        if auction and auction.is_active:
            auction.is_active = False
            db.session.commit()

            # Se il vincitore è diverso dall'emittente, aggiungi i soldi della puntata all'issuer dell'asta
            if auction.current_user_winner_id and auction.current_user_winner_id != auction.issuer_id:
                add_funds_response = requests.patch(
                    f"{AUTH_SERVICE_URL}/players/{auction.issuer_id}/currency/update",
                    json={'amount': auction.current_bid}
                )
                if add_funds_response.status_code != 200:
                    print(f"Failed to add funds to the issuer {auction.issuer_id} for auction {auction_id}")
                else:
                    print(f"Funds from the auction successfully added to issuer {auction.issuer_id}")

            # Assegnare il gacha all'utente vincitore usando l'endpoint update_owner in gacha_service
            if auction.current_user_winner_id:
                update_owner_response = requests.patch(
                    f"{GACHA_SERVICE_URL}/players/{auction.current_user_winner_id}/gachas/{auction.gacha_id}/update_owner"
                )

                if update_owner_response.status_code != 200:
                    print(f"Failed to transfer ownership of gacha {auction.gacha_id} to the winner of auction {auction_id}")
                else:
                    print(f"Gacha {auction.gacha_id} successfully transferred to user {auction.current_user_winner_id}")






if __name__ == 'main':
    app.run(debug=True)