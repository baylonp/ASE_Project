import requests
from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime, timezone
from functools import wraps
import jwt
import os
import base64
from werkzeug.utils import secure_filename
 
app = Flask(__name__)
 
# Configurazione dell'URL del servizio di autenticazione
AUTH_SERVICE_URL = 'http://authentication:5000' 
GACHA_SERVICE_URL = 'http://gacha_service:5000'
ADMIN_SERVICE_URL = 'http://admin_service:5000/admin_service/verify_admin'

 
# Configurazione del database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/gacha_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
 
# Inizializza SQLAlchemy
db = SQLAlchemy(app)
 
# Decoratore per proteggere gli endpoint con autenticazione JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')  # Il token deve essere inviato nell'header della richiesta
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']  # Ricaviamo l'ID utente dal token
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user_id, token, *args, **kwargs)  # Passiamo l'ID utente e il token come parametro
    return decorated
 
# Definizione del modello Pilot
class Pilot(db.Model):
    tablename = 'pilots'
    id = db.Column(db.Integer, primary_key=True)
    pilot_name = db.Column(db.String(80), nullable=False)
    rarity = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    ability = db.Column(db.String(200), nullable=False)
 
    def __repr__(self):
        return f'<Pilot {self.pilot_name}>'
 
# Definizione del modello Transaction
class Transaction(db.Model):
    tablename = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    amount_spent = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
 
    def __repr__(self):
        return f'<Transaction {self.id}, User {self.user_id}, Amount Spent {self.amount_spent}>'
 
# Creazione del database (se necessario) e popolazione iniziale
with app.app_context():
    db.create_all()
 
    # Popolamento del database con i dati dei piloti, se non già presenti
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

@app.route('/market_service/admin/gachas/<gacha_id>', methods=['PATCH'])
@token_required
def update_gacha_catalog(current_user_id, token, gacha_id):
    # Verifica che l'utente sia effettivamente un admin
    try:
        verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token})
        if verify_response.status_code != 200:
            return jsonify({'message': 'Unauthorized access'}), 403
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'An error occurred while communicating with the admin service: {str(e)}'}), 500

    # Aggiorna il gacha nel catalogo
    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    try:
        gacha = Pilot.query.filter_by(id=gacha_id).first()
        if not gacha:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)

        # Aggiorna i campi forniti nel corpo della richiesta
        if 'pilot_name' in data:
            gacha.pilot_name = data['pilot_name']
        if 'rarity' in data:
            gacha.rarity = data['rarity']
        if 'experience' in data:
            gacha.experience = data['experience']
        if 'ability' in data:
            gacha.ability = data['ability']

        db.session.commit()
        return make_response(jsonify({'message': 'Gacha updated successfully'}), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

 
@app.route('/market_service/players/<userId>/transactions', methods=['GET'])
@token_required
def get_user_transactions(current_user_id, token, userId):
    """
    Restituisce lo storico delle transazioni per un utente specifico.
    """
    # Check if the Token UserId matches (AccountID)
    # 403: Forbidden
    if (current_user_id != userId): 
        return make_response(jsonify({'message': 'Unauthorized access'}), 403)
    
    try:
        # Recupera tutte le transazioni per l'utente specificato
        transactions = Transaction.query.filter_by(user_id=userId).all()
 
        if not transactions:
            return make_response(jsonify({'message': 'No transactions found for this user'}), 404)
 
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
@token_required
def buy_in_game_currency(current_user_id, token, playerId):
    """
    Compra la valuta di gioco per il wallet del giocatore specificato.
    """
    try:
        if str(current_user_id) != playerId:
            return jsonify({'message': 'Unauthorized access'}), 403
 
        amount = request.args.get('amount', type=float)
 
        if amount is None or amount <= 0:
            return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)
 
        headers = {'x-access-token': token}  # Aggiungi il token all'header
        response = requests.patch(
            f"{AUTH_SERVICE_URL}/authentication/players/{playerId}/currency/update",
            json={'amount': amount},
            headers=headers
        )
 
        if response.status_code == 200:
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
    
### IMAGE SERVING ###
@app.route('/market_service/catalog', methods=['GET'])
@token_required
def get_catalog(current_user_id, token):
    """
    Restituisce il catalogo completo delle immagini (gachas).
    """
    try:
        image_folder = '/app/images'  # Directory where images are stored in the container
        image_files = os.listdir(image_folder)

        if not image_files:
            return make_response(jsonify({'message': 'No images available in the catalog'}), 404)

        image_data = []

        for image_file in image_files:
            if image_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(image_folder, image_file)
                
                # Open the image file and convert to base64 encoding
                with open(file_path, "rb") as img_file:
                    encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
                
                image_data.append({
                    'image_name': secure_filename(image_file),
                    'image_base64': encoded_image
                })

        return make_response(jsonify(image_data), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

### FINE IMAGE SERVING ####



''' 
@app.route('/market_service/catalog', methods=['GET'])
@token_required
def get_catalog(current_user_id, token):
    """
    Restituisce il catalogo completo dei piloti (gachas).
    """
    try:
        pilots = Pilot.query.all()
 
        if not pilots:
            return make_response(jsonify({'message': 'No pilots available in the catalog'}), 404)
 
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
    
'''   
 
# Endpoint per acquistare una roll (gacha)
@app.route('/market_service/players/<playerId>/gacha/roll', methods=['POST'])
@token_required
def buy_gacha_roll(current_user_id, token, playerId):
    """
    Consente all'utente di acquistare una roll (gacha) per ottenere un pilota casuale.
    """
    try:
        if str(current_user_id) != playerId:
            return jsonify({'message': 'Unauthorized access'}), 403
 
        ROLL_COST = 100
 
        headers = {'x-access-token': token}  # Aggiungi il token all'header
        response = requests.get(f"{AUTH_SERVICE_URL}/authentication/players/{playerId}", headers=headers)
 
        if response.status_code == 404:
            return make_response(jsonify({'message': 'Player not found'}), 404)
 
        user_data = response.json()
        user_wallet = user_data.get('wallet', 0)
 
        if user_wallet < ROLL_COST:
            return make_response(jsonify({'message': 'Not enough in-game currency to purchase a roll'}), 400)
 
        pilots = Pilot.query.all()
        if not pilots:
            return make_response(jsonify({'message': 'No pilots available'}), 404)
 
        selected_pilot = random.choice(pilots)
 
        update_response = requests.patch(
            f"{AUTH_SERVICE_URL}/authentication/players/{playerId}/currency/update",
            json={'amount': -ROLL_COST},
            headers=headers
        )
 
        if update_response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to update user wallet'}), 500)
 
        gacha_data = {
            "gacha_id": selected_pilot.id,
            "pilot_name": selected_pilot.pilot_name,
            "rarity": selected_pilot.rarity,
            "experience": selected_pilot.experience,
            "ability": selected_pilot.ability
        }
 
        add_gacha_response = requests.post(
            f"{GACHA_SERVICE_URL}/gacha_service/players/{playerId}/gachas",
            json=gacha_data,
            headers=headers
        )
 
        if add_gacha_response.status_code != 201:
            return make_response(jsonify({'message': 'Failed to add gacha to user collection'}), 500)
 
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
 
if __name__ == '__main__':
    app.run(debug=True)