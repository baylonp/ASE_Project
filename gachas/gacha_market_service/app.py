import requests
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
import random
from datetime import datetime, timezone

# Configurazione dell'URL del servizio di autenticazione
AUTH_SERVICE_URL = 'http://authentication:5000' 
GACHA_SERVICE_URL = 'http://gacha_service:5000'

# Configurazione del database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/gacha_market.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/transaction_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inizializza SQLAlchemy
db = SQLAlchemy(app)


# Definizione del modello Pilot
class Pilot(db.Model):
    tablename = 'pilots'
    id = db.Column(db.Integer, primary_key=True)
    pilot_name = db.Column(db.String(80), nullable=False)
    rarity = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    ability = db.Column(db.String(200), nullable=False)

    def repr(self):
        return f'<Pilot {self.pilot_name}>'
    

# Definizione del modello Transaction
class Transaction(db.Model):
    tablename = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    amount_spent = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def repr(self):
        return f'<Transaction {self.id}, User {self.user_id}, Amount Spent {self.amount_spent}>'


# Creazione del database (se necessario) e popolazione iniziale
with app.app_context():
    db.create_all()

    # Dati dei piloti da popolare nel database al momento della creazione della tabella

    pilots_data = [
        {"pilot_name": "Max Verstappen", "rarity": "Leggendaria", "experience": 95, "ability": "Dominatore assoluto nelle situazioni di alta pressione, aggressivo e veloce"},
        {"pilot_name": "Charles Leclerc", "rarity": "Leggendaria", "experience": 92, "ability": "Eccellente nelle qualifiche e in grado di trarre il meglio dalla vettura anche in situazioni difficili"},
        {"pilot_name": "Carlos Sainz", "rarity": "Epica", "experience": 88, "ability": "Costante e metodico, specialista delle strategie di gara che lo portano a rimontare costantemente"},
        {"pilot_name": "Lando Norris", "rarity": "Epica", "experience": 87, "ability": "Competitivo in ogni situazione, eccelle nelle condizioni difficili come la pioggia"},
        {"pilot_name": "Oscar Piastri", "rarity": "Rara", "experience": 78, "ability": "Pilota emergente che mostra grande promessa e crescita nelle prestazioni"},
        {"pilot_name": "Lewis Hamilton", "rarity": "Leggendaria", "experience": 98, "ability": "Esperto in battaglie ruota a ruota e in situazioni di alta pressione, con abilità straordinarie nelle rimonte"},
        {"pilot_name": "George Russel", "rarity": "Epica", "experience": 85, "ability": "Pilota consistente, capace di estrarre grandi prestazioni anche dalle vetture meno competitive"},
        {"pilot_name": "Sergio Perez", "rarity": "Rara", "experience": 84, "ability": "Specialista nella gestione delle gomme, ottimizza la durata degli stint"},
        {"pilot_name": "Fernando Alonso", "rarity": "Leggendaria", "experience": 97, "ability": "Maestro delle strategie e delle difese, esperto nell'adattarsi alle situazioni di gara"},
        {"pilot_name": "Nico Hulkenberg", "rarity": "Rara", "experience": 80, "ability": "Consolidato nel centro gruppo, ottiene punti preziosi in ogni occasione"},
        {"pilot_name": "Lance Stroll Jr.", "rarity": "Rara", "experience": 77, "ability": "Abile nelle partenze, ottiene buone posizioni nelle prime fasi di gara"},
        {"pilot_name": "Yuki Tsunoda", "rarity": "Comune", "experience": 73, "ability": "Competitivo, ma ancora in cerca di consistenza nel lungo periodo"},
        {"pilot_name": "Alex Albon", "rarity": "Rara", "experience": 79, "ability": "Abile nelle rimonte, riesce a ottenere buoni risultati anche con vetture meno competitive"},
        {"pilot_name": "Daniel Ricciardo", "rarity": "Epica", "experience": 85, "ability": "Esperto nei sorpassi audaci, molto efficace in situazioni di duello ruota a ruota"},
        {"pilot_name": "Kevin Magnussen", "rarity": "Comune", "experience": 74, "ability": "Aggressivo nelle prime fasi della gara, sempre pronto al combattimento"},
        {"pilot_name": "Pierre Gasly", "rarity": "Epica", "experience": 82, "ability": "Capace di ottenere il massimo risultato quando la situazione lo richiede"},
        {"pilot_name": "Esteban Ocon", "rarity": "Rara", "experience": 80, "ability": "Pilota consistente, sempre in grado di ottenere punti in condizioni stabili"},
        {"pilot_name": "Valtteri Bottas", "rarity": "Epica", "experience": 86, "ability": "Capace di supportare strategie di squadra complesse, eccelle nei long run"},
        {"pilot_name": "Zhou Guanyu", "rarity": "Comune", "experience": 72, "ability": "Pilota in crescita, sempre più consistente e sicuro nelle sue performance"},
        {"pilot_name": "Franco Colapinto", "rarity": "Comune", "experience": 70, "ability": "Promessa emergente, con grandi potenzialità per il futuro"}
    ]

    # Popolamento del database con i dati dei piloti, se non già presenti
    for pilot in pilots_data:
        existing_pilot = Pilot.query.filter_by(pilot_name=pilot['pilot_name']).first()
        if not existing_pilot:
            new_pilot = Pilot(
                pilot_name=pilot['pilot_name'],
                rarity=pilot['rarity'],
                experience=pilot['experience'],
                ability=pilot['ability']
            )
            db.session.add(new_pilot)
    
    db.session.commit()

### ADMIN ###

@app.route('/market_service/players/<userId>/transactions', methods=['GET'])
def get_user_transactions(userId):
    """
    Restituisce lo storico delle transazioni per un utente specifico.
    """
    try:
        # Recupera tutte le transazioni per l'utente specificato
        transactions = Transaction.query.filter_by(user_id=userId).all()

        # Controlla se ci sono transazioni per questo utente
        if not transactions:
            return make_response(jsonify({'message': 'No transactions found for this user'}), 404)

        # Prepara i risultati da restituire
        result = [
            {
                'id': transaction.id,
                'user_id': transaction.user_id,
                'amount_spent': transaction.amount_spent,
                'timestamp': transaction.timestamp.isoformat()
            } for transaction in transactions
        ]

        return make_response(jsonify(result), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)


### FINE ADMIN ###

@app.route('/market_service/players/<playerId>/currency/buy', methods=['POST'])
def buy_in_game_currency(playerId):
    """
    Compra la valuta di gioco per il wallet del giocatore specificato.
    ---
    """
    try:
        # Ottenere l'importo dalla query string
        amount = request.args.get('amount', type=float)

        # Validare l'importo specificato
        if amount is None or amount <= 0:
            return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)

        # Effettuare una richiesta POST al servizio di autenticazione per aggiornare il wallet dell'utente
        response = requests.post(
            f"{AUTH_SERVICE_URL}/players/{playerId}/currency/add",
            params={'amount': amount}
        )

        # Gestire la risposta del servizio di autenticazione
        if response.status_code == 200:

            # Creare una nuova transazione nel database delle transazioni
            new_transaction = Transaction(
                user_id=playerId,
                amount_spent=amount,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(new_transaction)
            db.session.commit()


            return make_response(jsonify({'message': 'In-game currency purchased successfully'}), 200)
        elif response.status_code == 404:
            return make_response(jsonify({'message': 'Player not found'}), 404)
        else:
            return make_response(jsonify({'message': 'Failed to add currency'}), response.status_code)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the auth service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
    
    
    
@app.route('/market_service/catalog', methods=['GET'])
def get_catalog():
    """
    Restituisce il catalogo completo dei piloti (gachas).
    """
    try:
        # Recupera tutti i piloti dal database
        pilots = Pilot.query.all()
        
        if not pilots:
            return make_response(jsonify({'message': 'No pilots available in the catalog'}), 404)

        # Prepara i risultati da restituire
        result = [
            {
                'gacha_id': pilot.id,
                'pilot_name': pilot.pilot_name,
                'rarity': pilot.rarity,
                'experience': pilot.experience,
                'ability': pilot.ability
            } for pilot in pilots
        ]

        return make_response(jsonify(result), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

# Endpoint per acquistare una roll (gacha)
@app.route('/market_service/players/<playerId>/gacha/roll', methods=['POST'])
def buy_gacha_roll(playerId):
    """
    Consente all'utente di acquistare una roll (gacha) per ottenere un pilota casuale.
    L'utente spende una quantità fissa di in-game currency per ottenere il pilota.
    ---
    """
    try:
        # Importo fisso della roll
        ROLL_COST = 100

        # Effettuare una richiesta al servizio di autenticazione per verificare il wallet dell'utente
        response = requests.get(f"{AUTH_SERVICE_URL}/players/{playerId}")

        if response.status_code == 404:
            return make_response(jsonify({'message': 'Player not found'}), 404)

        user_data = response.json()
        user_wallet = user_data.get('wallet', 0)

        # Verificare se l'utente ha abbastanza in-game currency
        if user_wallet < ROLL_COST:
            return make_response(jsonify({'message': 'Not enough in-game currency to purchase a roll'}), 400)

        # Scegliere un pilota casuale dal database
        pilots = Pilot.query.all()
        if not pilots:
            return make_response(jsonify({'message': 'No pilots available'}), 404)

        selected_pilot = random.choice(pilots)
        
        # Aggiornare il wallet dell'utente
        update_response = requests.patch(
            f"{AUTH_SERVICE_URL}/players/{playerId}/currency/update",
            json={'amount': -ROLL_COST}  # Sottrarre l'importo della roll dal wallet
        )

        if update_response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to update user wallet'}), 500)

        # Aggiungi il pilota alla collezione dell'utente chiamando il microservizio gacha_service
        gacha_data = {
            "gacha_id": selected_pilot.id,
            "pilot_name": selected_pilot.pilot_name,
            "rarity": selected_pilot.rarity,
            "experience": selected_pilot.experience,
            "ability": selected_pilot.ability
        }

        add_gacha_response = requests.post(
            f"{GACHA_SERVICE_URL}/players/{playerId}/gachas",
            json=gacha_data
        )

        if add_gacha_response.status_code != 201:
            return make_response(jsonify({'message': 'Failed to add gacha to user collection'}), 500)

        # Restituire il pilota ottenuto
        return make_response(jsonify({
            'message': 'Roll purchased successfully',
            'pilot': {
                'id': selected_pilot.id,
                'pilot_name': selected_pilot.pilot_name,
                'rarity': selected_pilot.rarity,
                'experience': selected_pilot.experience,
                'ability': selected_pilot.ability
            }
        }), 200)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the auth or gacha service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

if __name__ == 'main':
    app.run(debug=True)