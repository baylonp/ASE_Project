from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from bcrypt import checkpw, gensalt, hashpw
from datetime import datetime, timezone, timedelta
import jwt
import requests
from functools import wraps
from requests.exceptions import Timeout, RequestException
import base64
import json
import os
 
# Configura l'app Flask
app = Flask(__name__)
 
# Configurazione del database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable not set!")
app.config['SECRET_KEY'] = secret_key
 
# Inizializza il database
db = SQLAlchemy(app)

GACHA_MARKET_SERVICE_URL = 'https://gacha_market_service:5000/market_service/admin/gachas'
AUTH_SERVICE_URL = 'https://authentication_service:5000'
GACHA_SERVICE_URL = 'https://gacha_service:5000/gacha_service/admin/update_all'
 
# Definizione del modello Admin
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    jwt_token = db.Column(db.String(500), nullable=True)
 
# Creazione del database e aggiunta dell'account admin hardcoded
with app.app_context():
    db.create_all()
    # Admin hardcoded - username: "admin", password: "admin"
    existing_admin = Admin.query.filter_by(username='admin').first()
    if not existing_admin:
        hashed_password = hashpw('admin'.encode('utf-8'), gensalt())
        admin = Admin(username='admin', password=hashed_password.decode('utf-8'), jwt_token=None)
        db.session.add(admin)
        db.session.commit()
 
# Funzione per creare un token JWT per l'admin
# Admin Token has admin_id field
def generate_jwt(admin):
    payload = {
        'admin_id': admin.id,
        'username': admin.username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=2)  # Scadenza del token in 2 ore
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

# Compare if two datetime objects are close enough (tolerance of 1 second)
def compare_datetimes(dt1, dt2, tolerance_seconds=1):
    return abs((dt1 - dt2).total_seconds()) <= tolerance_seconds
 
def compare_two_jwt(token1, token2, payload1, payload2):
    # Split the JWTs into header, payload, and signature
    if len(token1.split(".")) != 3 or len(token2.split(".")) != 3:
        return False  # Invalid token format
 
    # Extract the signature (third part of the JWT)
    signature1 = token1.split(".")[2]
    signature2 = token2.split(".")[2]
 
    # Compare Signatures
    checkSign = (signature1 == signature2)
 
    # Compare Payloads
    if payload1 is None or payload2 is None:
        return False
 
    # Normalize 'exp' field (if it's a datetime)
    if 'exp' in payload1 and 'exp' in payload2:
        payload1['exp'] = datetime.fromtimestamp(payload1['exp'], tz=timezone.utc).replace(microsecond=0)
        payload2['exp'] = datetime.fromtimestamp(payload2['exp'], tz=timezone.utc).replace(microsecond=0)
 
    # Check if the payloads are identical
    checkPayloadsQuality = (payload1 == payload2)
 
    # Compare specific fields with tolerance (like 'admin_id', 'username', 'exp')
    checkPayloadsTolerance = (payload1.get('admin_id') == payload2.get('admin_id') and
                              payload1.get('username') == payload2.get('username') and
                              compare_datetimes(payload1['exp'], payload2['exp']))
 
    # Return True if all checks pass
    return (checkSign and checkPayloadsQuality and checkPayloadsTolerance)

# Decoratore per proteggere gli endpoint (solo admin)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Decode HTTP Received Token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_admin = Admin.query.filter_by(id=data['admin_id']).first()
            if current_admin is None:
                raise jwt.InvalidTokenError
            # Extract User JWT Token From the AdminDB
            if (current_admin.jwt_token is None):
                return jsonify({'message': 'Forbidden Token for Logged OUT Admin!'}), 403
            # Decode User JWT to check for Errors
            tokenAdmin = jwt.decode(current_admin.jwt_token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # Check The Two Tokens Signatures
            if not compare_two_jwt(token, current_admin.jwt_token, data, tokenAdmin):
                return jsonify({'message': 'Forbidden Token for Logged IN Admin!'}), 403
            # We are OK.
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_admin, token,  *args, **kwargs)
    return decorated
 
# Endpoint per il login dell'admin
@app.route('/admin_service/auth', methods=['POST'])
def admin_login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    admin = Admin.query.filter_by(username=data['username']).first()
    if admin and checkpw(data['password'].encode('utf-8'), admin.password.encode('utf-8')):
        token = generate_jwt(admin)
        # Add Token to Admin
        admin.jwt_token = token
        db.session.commit()
        return make_response(jsonify({'message': 'Login successful', 'token': token}), 200)
 
    return make_response(jsonify({'message': 'Invalid credentials'}), 401)

@app.route('/admin_service/logout', methods=['PATCH'])
@token_required
def logout(current_admin, token):
    admin_id = request.args.get('adminId')
    if not admin_id:
        return make_response(jsonify({'message': 'Admin ID is required'}), 400)
 
    # Find the user by ID and clear the jwt_token field
    admin = Admin.query.get(admin_id)
    if not admin:
        return make_response(jsonify({'message': 'Admin not found'}), 404)
 
    # Remove the Session JWT Token
    admin.jwt_token = None 
    db.session.commit()
    return make_response(jsonify({'message': 'Logout successful', 'adminId': admin.id}), 200)

@app.route('/admin_service/adminId', methods=['GET'])
@token_required
def get_admin_id(current_admin, token):
    username = request.args.get('username')
 
    if not username:
        return make_response(jsonify({'message': 'Username is required'}), 400)
 
    admin = Admin.query.filter_by(username=username).first()
    if not admin:
        return make_response(jsonify({'message': 'Admin not found'}), 404)
 
    return jsonify({'adminId': admin.id}), 200

# Endpoint per verificare se l'utente è un admin (usato da altri microservizi)
@app.route('/admin_service/verify_admin', methods=['GET'])
@token_required
def verify_admin(curr_admin, admin_token):
    # check for @token_required unseen errors
    if admin_token is None or curr_admin is None: 
        return make_response(jsonify({'message': 'Bad Request. Something happened on Admin Token Vaerification.'}), 400) # Bad Request
    
    # @token_required has verified that we have received a valid token.
    return make_response(jsonify({'message': 'Ok.'}), 200) # OK
 

# Endpoint per ottenere informazioni su un utente (richiede token)
@app.route('/admin_service/user_info/<playerId>', methods=['GET'])
@token_required
def get_user_info(current_admin, token, playerId):
    # Effettua una richiesta al servizio di autenticazione per ottenere le informazioni sull'utente
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/authentication/players/{playerId}",
                                headers={'x-access-token': token}, verify=False, timeout=5)
        if response.status_code == 200:
            return make_response(jsonify(response.json()), 200)
        elif response.status_code == 404:
            return make_response(jsonify({'message': 'Player not found'}), 404)
        else:
            return make_response(jsonify(response.json()), response.status_code)
    except Timeout:
        return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the authentication service: {str(e)}'}), 500)
    


# Endpoint per modificare un Gacha nel catalogo e aggiornare la collezione degli utenti
@app.route('/admin_service/gachas/<gacha_id>', methods=['PATCH'])
@token_required
def update_gacha(current_admin, token, gacha_id):
    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    # Effettua una richiesta al gacha_market_service per aggiornare il catalogo
    
    try:
        
        response = requests.patch(f"{GACHA_MARKET_SERVICE_URL}/{gacha_id}",
                                headers={'x-access-token': token}, json=data, verify=False, timeout=5)
        if response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to update gacha in catalog',}), response.status_code)

        # Effettua una richiesta al gacha_service per aggiornare la collezione degli utenti
        
        update_response = requests.patch(f"{GACHA_SERVICE_URL}/{gacha_id}", json=data, headers={'x-access-token': request.headers.get('x-access-token')},verify=False, timeout=5)
        if update_response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to update gacha in user collections'}), update_response.status_code)
        

        return make_response(jsonify({'message': 'Gacha updated successfully'}), 200)
    except Timeout:
            return make_response(jsonify({'message': 'Authentication service is temporarily unavailable'}), 503)  # Service Unavailable
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha market or gacha service: {str(e)}'}), 500)
    
    # Endpoint per ottenere l'intero database delle collezioni dal gacha_service (solo per admin)

@app.route('/admin_service/all_collections', methods=['GET'])
@token_required
def get_all_gacha_collections(current_admin, token):
    """
    Permette all'admin di ottenere tutte le collezioni Gacha presenti nel database del gacha_service
    """  
    try:
        # Effettua una richiesta al gacha_service per ottenere tutte le collezioni, con un timeout di 5 secondi
        response = requests.get(
            f"https://gacha_service:5000/gacha_service/admin/collections",
            headers={'x-access-token': token},
            verify=False,
            timeout=5  # Timeout in secondi
        )
        
        if response.status_code == 200:
            return make_response(jsonify(response.json()), 200)
        elif response.status_code == 204:
            return make_response(jsonify({'message': 'No Gacha collections found'}), 204)
        else:
            return make_response(jsonify({'message': 'Failed to retrieve collections from gacha_service'}), response.status_code)

    except Timeout:
        # Gestione del timeout
        return make_response(jsonify({'message': 'The request to gacha_service timed out'}), 504)

    except requests.exceptions.RequestException as e:
        # Gestione di altre eccezioni durante la richiesta
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha service: {str(e)}'}), 500)


# Endpoint per aggiungere un nuovo gacha al catalogo tramite il gacha_market_service (solo per admin)
@app.route('/admin_service/gachas', methods=['POST'])
@token_required
def add_gacha_to_catalog(current_admin, token):
    """
    Permette agli amministratori di aggiungere un nuovo gacha al catalogo tramite il gacha_market_service
    """
    # Ottieni i dati per il nuovo gacha
    data = request.json
    if not data or 'pilot_name' not in data or 'rarity' not in data or 'experience' not in data or 'ability' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    try:
        # Effettua una richiesta al gacha_market_service per aggiungere il nuovo gacha al catalogo
        response = requests.post(
            f"https://gacha_market_service:5000/market_service/admin/gachas",
            headers={'x-access-token': token},
            json=data,
            verify=False,
            timeout=5
        )
        
        if response.status_code == 201:
            return make_response(jsonify({'message': 'Gacha added successfully'}), 201)
        else:
            return make_response(jsonify({'message': 'Failed to add gacha', 'details': response.json()}), response.status_code)

    except Timeout:
        return make_response(jsonify({'message': 'The request to gacha_market_service timed out'}), 503)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha_market_service: {str(e)}'}), 500)


# Endpoint per rimuovere un gacha dal catalogo tramite il gacha_market_service (solo per admin)
@app.route('/admin_service/gachas/<int:gacha_id>', methods=['DELETE'])
@token_required
def remove_gacha_from_catalog(current_admin, token, gacha_id):
    """
    Permette agli amministratori di rimuovere un gacha dal catalogo tramite il gacha_market_service
    """
    try:
        # Effettua una richiesta al gacha_market_service per rimuovere il gacha dal catalogo
        response = requests.delete(
            f"https://gacha_market_service:5000/market_service/admin/gachas/{gacha_id}",
            headers={'x-access-token': token},
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            return make_response(jsonify({'message': 'Gacha removed successfully'}), 200)
        elif response.status_code == 404:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)
        else:
            return make_response(jsonify({'message': 'Failed to remove gacha', 'details': response.json()}), response.status_code)

    except Timeout:
        return make_response(jsonify({'message': 'The request to gacha_market_service timed out'}), 503)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha_market_service: {str(e)}'}), 500)


@app.route('/admin_service/transactions/<userId>', methods=['GET'])
@token_required
def get_user_transactions_via_admin_service(current_admin, token, userId):
    """
    Permette all'amministratore di ottenere lo storico delle transazioni di un utente specifico tramite il gacha_market_service
    """
    try:
        # Effettua una richiesta al gacha_market_service per ottenere le transazioni dell'utente specifico
        response = requests.get(
            f"https://gacha_market_service:5000/market_service/admin/transactions/{userId}",
            headers={'x-access-token': token},
            verify=False,
            timeout=5
        )

        if response.status_code == 200:
            return make_response(jsonify(response.json()), 200)
        elif response.status_code == 404:
            return make_response(jsonify({'message': 'No transactions found for this user'}), 404)
        elif response.status_code == 403:
            return make_response(jsonify({'message': 'Unauthorized access'}), 403)
        else:
            return make_response(jsonify({'message': 'Failed to retrieve transactions from gacha_market_service'}), response.status_code)

    except Timeout:
        return make_response(jsonify({'message': 'The request to gacha_market_service timed out'}), 503)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha_market_service: {str(e)}'}), 500)


# Punto di ingresso dell'app
if __name__ == '__main__':
    app.run()