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
    issuer_id = db.Column(db.String, nullable=False)
    current_user_winner = db.Column(db.String, nullable=True, default=None)
    current_bid = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def repr(self):
        return f'<Auction {self.auction_id}, Gacha {self.gacha_id}, Issuer {self.issuer_id}>'

# Creazione del database
with app.app_context():
    db.create_all()

GACHA_SERVICE_URL = 'http://gacha_service:5000'

@app.route('/players/<userId>/setAuction', methods=['POST'])
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
            current_bid=base_price,
            is_active=True,
            start_time=datetime.now(timezone.utc)  # Timestamp in UTC

        )

        db.session.add(new_auction)
        db.session.commit()

        # Attivare un timer per disattivare l'asta dopo 1 minuto
        auction_id = new_auction.auction_id
        timer = threading.Timer(60.0, end_auction, [auction_id])
        timer.start()

        return make_response(jsonify({'message': 'Auction created successfully', 'auction_id': auction_id}), 201)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)


@app.route('/auctions/active', methods=['GET'])
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
                'current_bid': auction.current_bid,
                'start_time': auction.start_time.isoformat()  # Convertire il timestamp in un formato leggibile
            })

        return make_response(jsonify(result), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)



def end_auction(auction_id):
    """
    Funzione per disattivare l'asta dopo 1 minuto
    """
    with app.app_context():
        auction = Auction.query.get(auction_id)
        if auction and auction.is_active:
            auction.is_active = False
            db.session.commit()





if __name__ == 'main':
    app.run(debug=True)