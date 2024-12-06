from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import requests
import jwt
from functools import wraps
from requests.exceptions import Timeout, RequestException
import os
 
app = Flask(__name__)
 
# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/issuedANDownedDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable not set!")
app.config['SECRET_KEY'] = secret_key
 
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

# Definizione del modello GachaCollection
class GachaCollection(db.Model):
    tablename = 'gacha_collection'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    gacha_id = db.Column(db.Integer, nullable=False)
    pilot_name = db.Column(db.String, nullable=False)
    rarity = db.Column(db.String, nullable=False)
    experience = db.Column(db.String, nullable=False)
    ability = db.Column(db.String, nullable=False)
 
# Creazione del database
with app.app_context():
    db.create_all()
 
GACHA_MARKET_SERVICE_URL = 'https://gacha_market_service:5000/market_service/catalog'
ADMIN_SERVICE_URL = 'https://admin_service:5000/admin_service/verify_admin'
 
@app.route('/gacha_service/players/<userID>/gachas', methods=['GET', 'DELETE'])
@token_required
def handle_user_gachas(current_user_id, token, userID):
    if request.method == 'GET':
        # Esistente: restituisce la collezione di gachas di un giocatore specifico
        gachas = GachaCollection.query.filter_by(user_id=userID).all()
        if not gachas:
            return make_response(jsonify({'message': 'Player does not own any Gachas'}), 204)
 
        result = []
        for gacha in gachas:
            result.append({
                'gachaId': gacha.gacha_id,
                'name': gacha.pilot_name,
                'rarity': gacha.rarity,
                'experience':gacha.experience,
                'ability':gacha.ability
            })
 
        return jsonify(result), 200
 
    elif request.method == 'DELETE':
       
        try:
            user_gachas = GachaCollection.query.filter_by(user_id=userID).all()
            if not user_gachas:
                return make_response(jsonify({'message': 'No Gacha collection found for this user'}), 404)
 
            # Cancellare tutte le gachas associate all'utente
            for gacha in user_gachas:
                db.session.delete(gacha)
 
            db.session.commit()
 
            return make_response(jsonify({'message': 'Gacha collection deleted successfully'}), 200)
 
        except Exception as e:
            return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
 
@app.route('/gacha_service/players/<userID>/gachas/<gachaId>', methods=['GET'])
@token_required
def get_specific_gacha(current_user_id, token, userID, gachaId):
    """
    Restituisce i dettagli di un gacha specifico della collezione di un giocatore
    """
    gacha = GachaCollection.query.filter_by(user_id=userID, gacha_id=gachaId).first()
    if not gacha:
        return make_response(jsonify({'message':'Gacha or player not found'}), 404)
 
    result = {
        'gachaId': gacha.gacha_id,
        'pilotName': gacha.pilot_name,
        'rarity': gacha.rarity,
        'experience': gacha.experience,
        'ability': gacha.ability
    }
 
    return jsonify(result), 200
 
@app.route('/gacha_service/players/<userID>/gachas', methods=['POST'])
@token_required
def add_gacha_to_player(current_user_id, token, userID):
    """
    Aggiunge un nuovo gacha alla collezione di un utente specifico
    """
    data = request.json
    if not data or 'gacha_id' not in data or 'pilot_name' not in data or 'rarity' not in data or 'experience' not in data or 'ability' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    # Crea un nuovo gacha per la collezione dell'utente
    new_gacha = GachaCollection(
        user_id=userID,
        gacha_id=data['gacha_id'],
        pilot_name=data['pilot_name'],
        rarity=data['rarity'],
        experience=data['experience'],
        ability=data['ability']
    )
 
    db.session.add(new_gacha)
    db.session.commit()
 
    return make_response(jsonify({'message': 'Gacha added successfully'}), 201)
 
@app.route('/gacha_service/players/<userID>/gachas/missing', methods=['GET'])
@token_required
def get_missing_gachas(current_user_id, token, userID):
    """
    Restituisce i gachas mancanti dalla collezione di un giocatore rispetto al catalogo completo
    """
    try:
        # Recuperare la collezione di gachas dell'utente
        user_gachas = GachaCollection.query.filter_by(user_id=userID).all()
        user_gacha_ids = {gacha.gacha_id for gacha in user_gachas}
 
        # Effettuare una richiesta al servizio gacha_market_service per ottenere il catalogo completo dei gachas
        headers = {'x-access-token': token}  
        try:
            response = requests.get(f"{GACHA_MARKET_SERVICE_URL}", headers=headers, verify=False, timeout=5)
    
            if response.status_code != 200:
                return make_response(jsonify({'message': 'Failed to retrieve the gacha catalog from gacha_market_service'}), 500)
        except Timeout:
                return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

            
        # Catalogo completo dei gachas
        catalog = response.json()
 
        # Trovare i gachas mancanti nella collezione dell'utente
        missing_gachas = [gacha for gacha in catalog if gacha['gacha_id'] not in user_gacha_ids]
 
        if not missing_gachas:
            return make_response(jsonify({'message': 'Player has all gachas'}), 200)
 
        return jsonify(missing_gachas), 200
 
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha market service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
 
@app.route('/gacha_service/players/<userID>/gachas/<gachaID>/update_owner', methods=['PATCH'])
@token_required
def update_gacha_owner(current_user_id, token, userID, gachaID):
    """
    Aggiorna l'user_id del gacha specificato nella collezione dell'utente
    """
    try:
        # Recuperare il gacha specifico dalla collezione in base al gachaID
        gacha = GachaCollection.query.filter_by(gacha_id=gachaID).first()
 
        # Controllo se il gacha esiste nel database
        if not gacha:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)
 
        # Aggiorna l'user_id del gacha
        gacha.user_id = userID
        db.session.commit()
 
        return make_response(jsonify({'message': 'Gacha ownership updated successfully'}), 200)
 
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
    

    ##Admin

# Endpoint per aggiornare un gacha nella collezione di tutti gli utenti (nuovo endpoint nel gacha_service)
@app.route('/gacha_service/admin/update_all/<gacha_id>', methods=['PATCH'])
@token_required
def update_gacha_for_all_users(cuurent_user, token, gacha_id):
    try:
        try:
            # Effettua una richiesta all'admin_service per verificare che l'utente sia un admin
            verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token}, verify=False, timeout=5)
            if verify_response.status_code != 200:
                return jsonify({'message': 'Unauthorized access'}), 403
            
        except Timeout:
                return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable

    
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'An error occurred while communicating with the admin service: {str(e)}'}), 500

    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
    
    try:
        # Recupera tutti i gacha degli utenti che corrispondono a gacha_id
        gachas = GachaCollection.query.filter_by(gacha_id=gacha_id).all()
        if not gachas:
            return make_response(jsonify({'message': 'No gacha found for given gacha_id'}), 404)
        
        # Aggiorna i parametri specificati per tutti i gacha trovati
        for gacha in gachas:
            if 'pilot_name' in data:
                gacha.pilot_name = data['pilot_name']
            if 'rarity' in data:
                gacha.rarity = data['rarity']
            if 'experience' in data:
                gacha.experience = data['experience']
            if 'ability' in data:
                gacha.ability = data['ability']
        
        db.session.commit()
        return make_response(jsonify({'message': 'Gacha updated for all users successfully'}), 200)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
    
@app.route('/gacha_service/admin/collections', methods=['GET'])
@token_required
def get_all_collections(curr_user, token):
    """
    Permette ad un admin di vedere tutto il database di Gacha Collection
    """
    try:
        # Effettua una richiesta all'admin_service per verificare che l'utente sia un admin
        verify_response = requests.get(ADMIN_SERVICE_URL, headers={'x-access-token': token},verify=False,timeout=5)
        if verify_response.status_code != 200:
            return jsonify({'message': 'Unauthorized access'}), 403

        # Se l'utente è un admin, recupera tutte le collezioni di Gacha
        gachas = GachaCollection.query.all()
        if not gachas:
            return make_response(jsonify({'message': 'No Gacha collections found'}), 204)

        # Prepara la risposta contenente tutte le collezioni di Gacha
        result = []
        for gacha in gachas:
            result.append({
                'id': gacha.id,
                'user_id': gacha.user_id,
                'gacha_id': gacha.gacha_id,
                'pilot_name': gacha.pilot_name,
                'rarity': gacha.rarity,
                'experience': gacha.experience,
                'ability': gacha.ability
            })

        return jsonify(result), 200
    except Timeout:
        return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable


    except requests.exceptions.RequestException as e:
        # Gestione di eventuali errori di comunicazione con il servizio admin_service
        return make_response(jsonify({'message': f'An error occurred while communicating with the admin service: {str(e)}'}), 500)

    except Exception as e:
        # Gestione di eventuali errori interni
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

 
if __name__ == '__main__':
    app.run()