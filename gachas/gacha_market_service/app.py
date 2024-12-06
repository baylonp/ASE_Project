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
from requests.exceptions import Timeout, RequestException

 
app = Flask(__name__)
 
# Configurazione dell'URL del servizio di autenticazione
AUTH_SERVICE_URL = 'https://authentication:5000' 
GACHA_SERVICE_URL = 'https://gacha_service:5000'
ADMIN_SERVICE_URL = 'https://admin_service:5000/admin_service/verify_admin'

 
# Configurazione del database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/gacha_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable not set!")
app.config['SECRET_KEY'] = secret_key
 
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
                    response = requests.get(admin_service_url, headers={'x-access-token': token}, verify=False,timeout=5)
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
        {"pilot_name": "Sergio Perez", "rarity": "Epica", "experience": 84, "ability": "Specialista nella gestione delle gomme, ottimizza la durata degli stint"},
        {"pilot_name": "Fernando Alonso", "rarity": "Epica", "experience": 97, "ability": "Maestro delle strategie e delle difese, esperto nell'adattarsi alle situazioni di gara"},
        {"pilot_name": "Nico Hulkenberg", "rarity": "Comune", "experience": 80, "ability": "Consolidato nel centro gruppo, ottiene punti preziosi in ogni occasione"},
        {"pilot_name": "Lance Stroll Jr.", "rarity": "Comune", "experience": 77, "ability": "Abile nelle partenze, ottiene buone posizioni nelle prime fasi di gara"},
        {"pilot_name": "Yuki Tsunoda", "rarity": "Comune", "experience": 73, "ability": "Competitivo, ma ancora in cerca di consistenza nel lungo periodo"},
        {"pilot_name": "Alex Albon", "rarity": "Comune", "experience": 79, "ability": "Abile nelle rimonte, riesce a ottenere buoni risultati anche con vetture meno competitive"},
        {"pilot_name": "Daniel Ricciardo", "rarity": "Rara", "experience": 85, "ability": "Esperto nei sorpassi audaci, molto efficace in situazioni di duello ruota a ruota"},
        {"pilot_name": "Kevin Magnussen", "rarity": "Comune", "experience": 74, "ability": "Aggressivo nelle prime fasi della gara, sempre pronto al combattimento"},
        {"pilot_name": "Pierre Gasly", "rarity": "Rara", "experience": 82, "ability": "Capace di ottenere il massimo risultato quando la situazione lo richiede"},
        {"pilot_name": "Esteban Ocon", "rarity": "Comune", "experience": 80, "ability": "Pilota consistente, sempre in grado di ottenere punti in condizioni stabili"},
        {"pilot_name": "Valtteri Bottas", "rarity": "Rara", "experience": 86, "ability": "Capace di supportare strategie di squadra complesse, eccelle nei long run"},
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
        try:
            verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token}, verify=False, timeout=5)
            if verify_response.status_code != 200:
                return jsonify({'message': 'Unauthorized access'}), 403
        except Timeout:
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable


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


@app.route('/market_service/admin/transactions/<userId>', methods=['GET'])
@token_required
def get_user_transactions_admin(current_user_id, token, userId):
    """
    Permette agli amministratori di vedere lo storico delle transazioni per un utente specifico.
    """
    # Verifica che l'utente sia effettivamente un admin
    try:
        verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token}, verify=False, timeout=5)
        if verify_response.status_code != 200:
            return jsonify({'message': 'Unauthorized access'}), 403
    except Timeout:
        return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'An error occurred while communicating with the admin service: {str(e)}'}), 500

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


 
# Endpoint per aggiungere un nuovo gacha al catalogo (solo per admin)
@app.route('/market_service/admin/gachas', methods=['POST'])
@token_required
def add_gacha(current_user_id, token):
    """
    Permette all'amministratore di aggiungere un nuovo gacha al catalogo
    """
    # Verifica che l'utente sia effettivamente un admin
    try:
        verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token}, verify=False, timeout=5)
        if verify_response.status_code != 200:
            return jsonify({'message': 'Unauthorized access'}), 403
    except Timeout:
        return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'An error occurred while communicating with the admin service: {str(e)}'}), 500

    # Ottieni i dati per il nuovo gacha
    data = request.json
    if not data or 'pilot_name' not in data or 'rarity' not in data or 'experience' not in data or 'ability' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    try:
        # Crea un nuovo gacha nel catalogo
        new_pilot = Pilot(
            pilot_name=data['pilot_name'],
            rarity=data['rarity'],
            experience=data['experience'],
            ability=data['ability']
        )
        db.session.add(new_pilot)
        db.session.commit()
        return make_response(jsonify({'message': 'Gacha added successfully', 'gacha_id': new_pilot.id}), 201)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)


# Endpoint per rimuovere un gacha dal catalogo (solo per admin)
@app.route('/market_service/admin/gachas/<int:gacha_id>', methods=['DELETE'])
@token_required
def remove_gacha(current_user_id, token, gacha_id):
    """
    Permette all'amministratore di rimuovere un gacha dal catalogo
    """
    # Verifica che l'utente sia effettivamente un admin
    try:
        verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token}, verify=False, timeout=5)
        if verify_response.status_code != 200:
            return jsonify({'message': 'Unauthorized access'}), 403
    except Timeout:
        return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'An error occurred while communicating with the admin service: {str(e)}'}), 500

    try:
        # Recupera il gacha dal catalogo e lo rimuove
        gacha = Pilot.query.filter_by(id=gacha_id).first()
        if not gacha:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)

        db.session.delete(gacha)
        db.session.commit()

        return make_response(jsonify({'message': 'Gacha removed successfully'}), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
 
### FINE ADMIN ###

@app.route('/market_service/players/<userId>/transactions', methods=['GET'])
@token_required
def get_user_transactions(current_user, token, userId):
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


 
@app.route('/market_service/players/<playerId>/currency/buy', methods=['POST'])
@token_required
def buy_in_game_currency(current_user_id, token, playerId):
    """
    Compra la valuta di gioco per il wallet del giocatore specificato.
    """
    try:
         
        amount = request.args.get('amount', type=float)
 
        if amount is None or amount <= 0:
            return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)
 
        headers = {'x-access-token': token}  # Aggiungi il token all'header
        try:
            response = requests.patch(
                f"{AUTH_SERVICE_URL}/authentication/players/{playerId}/currency/update",
                json={'amount': amount},
                headers=headers,
                verify=False,
                timeout=5
            )
        except Timeout:
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

 
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

'''   
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

# The Gacha Roll takes into consideration the Rarity of each Pilot
def get_random_pilot(pilots):
    # Example rarity weights (can be modified or made configurable)
    rarity_weights = {
        'Leggendaria': 5,
        'Epica': 10,
        'Rara': 20,
        'Comune': 65
    }

    # Extract unique rarities dynamically
    rarities = {pilot.rarity for pilot in pilots}

    # Build weights dynamically based on available rarities
    available_rarity_weights = [rarity_weights[rarity] for rarity in rarities]

    # Select a rarity based on weights
    selected_rarity = random.choices(list(rarities), weights=available_rarity_weights, k=1)[0]

    # Filter pilots by the selected rarity
    filtered_pilots = [pilot for pilot in pilots if pilot.rarity == selected_rarity]

    # Select a random pilot from the filtered list
    selected_pilot = random.choice(filtered_pilots)

    return selected_pilot
 
# Endpoint per acquistare una roll (gacha)
@app.route('/market_service/players/<playerId>/gacha/roll', methods=['POST'])
@token_required
def buy_gacha_roll(current_user_id, token, playerId):
    """
    Consente all'utente di acquistare una roll (gacha) per ottenere un pilota casuale.
    """
    try:

        ROLL_COST = 100
 
        headers = {'x-access-token': token} 
        try:
            response = requests.get(f"{AUTH_SERVICE_URL}/authentication/players/{playerId}", headers=headers,verify=False, timeout=5)
    
            if response.status_code == 404:
                return make_response(jsonify({'message': 'Player not found'}), 404)
        except Timeout:
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

            
 
        user_data = response.json()
        user_wallet = user_data.get('wallet', 0)
 
        if user_wallet < ROLL_COST:
            return make_response(jsonify({'message': 'Not enough in-game currency to purchase a roll'}), 400)
 
        pilots = Pilot.query.all()
        if not pilots:
            return make_response(jsonify({'message': 'No pilots available'}), 404)
    

        selected_pilot = get_random_pilot(pilots)
 
        try:
            update_response = requests.patch(
                f"{AUTH_SERVICE_URL}/authentication/players/{playerId}/currency/update",
                json={'amount': -ROLL_COST},
                headers=headers,
                verify=False,
                timeout=5
            )
        except Timeout:
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

 
        if update_response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to update user wallet'}), 500)
 
        gacha_data = {
            "gacha_id": selected_pilot.id,
            "pilot_name": selected_pilot.pilot_name,
            "rarity": selected_pilot.rarity,
            "experience": selected_pilot.experience,
            "ability": selected_pilot.ability
        }
 
        try:
            add_gacha_response = requests.post(
                f"{GACHA_SERVICE_URL}/gacha_service/players/{playerId}/gachas",
                json=gacha_data,
                headers=headers,
                verify=False,
                timeout=5
            )
 
            if add_gacha_response.status_code != 201:
                return make_response(jsonify({'message': 'Failed to add gacha to user collection'}), 500)
            
        except Timeout:

            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

 
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

 
    
@app.route('/market_service/showGacha/<int:gachaId>', methods=['GET'])
def show_gacha(gachaId):
    """
    Recupera le informazioni di un gacha specifico dato il suo ID.
    """
    try:
        # Recupera il gacha dal database
        gacha = Pilot.query.filter_by(id=gachaId).first()

        # Controlla se il gacha esiste
        if not gacha:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)

        # Prepara il risultato
        result = {
            'gacha_id': gacha.id,
            'pilot_name': gacha.pilot_name,
            'rarity': gacha.rarity,
            'experience': gacha.experience,
            'ability': gacha.ability
        }

        return make_response(jsonify(result), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)





 
if __name__ == '__main__':
    app.run()