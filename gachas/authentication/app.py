from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, gensalt, checkpw
import requests
from datetime import datetime, timezone, timedelta
import jwt
from functools import wraps
import base64
import json
from requests.exceptions import Timeout, RequestException
import re
import os
 
# Configura l'app Flask
app = Flask(__name__)
 
# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/users.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable not set!")
app.config['SECRET_KEY'] = secret_key
 
# Inizializza il database
db = SQLAlchemy(app)
 
# Funzione per creare un token JWT
def generate_jwt(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
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
 
    # Compare specific fields with tolerance (like 'user_id', 'username', 'exp')
    checkPayloadsTolerance = (payload1.get('user_id') == payload2.get('user_id') and
                              payload1.get('username') == payload2.get('username') and
                              compare_datetimes(payload1['exp'], payload2['exp']))
 
    # Return True if all checks pass
    return (checkSign and checkPayloadsQuality and checkPayloadsTolerance)
 
# Decoratore per proteggere gli endpoint
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
                current_user = User.query.filter_by(id=data['user_id']).first()
                if current_user is None:
                    raise jwt.InvalidTokenError
                # Extract User JWT Token From the UserDB
                if (current_user.jwt_token is None):
                    return jsonify({'message': 'Forbidden Token for Logged OUT User!'}), 403
                # Decode User JWT to check for Errors
                tokenUser = jwt.decode(current_user.jwt_token, app.config['SECRET_KEY'], algorithms=['HS256'])
                # Check The Two Tokens Signatures
                if not compare_two_jwt(token, current_user.jwt_token, data, tokenUser):
                    return jsonify({'message': 'Forbidden Token for Logged IN User!'}), 403
                # (User) We are OK.
                return f(current_user, token, *args, **kwargs)  # Passa il current_user e il token come argomento
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
 
# A Service has required the validation of a given Token
@app.route("/authentication/validate", methods=["GET"])
@token_required
def validate_service_token(curr_user, token):
    """Endpoint to validate JWT token."""
    # check for @token_required unseen errors
    if curr_user is None or token is None: 
        return make_response(jsonify({'message': 'Bad Request. Something happened on Token Vaerification.'}), 400) # Bad Request
    
    # @token_required has verified that we have received a valid token.
    return make_response(jsonify({'message': 'Ok.'}), 200) # OK

 
# Definizione del modello User
class User(db.Model):
    tablename = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    wallet = db.Column(db.Integer, nullable=False, default=0)
    jwt_token = db.Column(db.String(500), nullable=True)
 
    def repr(self):
        return f'<User {self.username}>'
 
# Crea il database se non esiste
with app.app_context():
    db.create_all()
 
GACHA_SERVICE_URL = 'https://gacha_service:5000'
ADMIN_SERVICE_URL = 'https://admin_service:5000/admin_service/verify_admin'
 
# Definizione degli endpoint
@app.route('/authentication/account', methods=['POST'])
def create_account():
    data = request.json
    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
    
    # Regex per validare lo username
    username_pattern = r'^[a-zA-Z0-9_.-]{3,20}$'
    if not re.match(username_pattern, data['username']):
        return make_response(jsonify({'message': 'Invalid username format. Only alphanumeric characters, underscores, dots, and hyphens are allowed. Length must be between 3 and 20.'}), 400)
    
    # Regex per validare la email
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_pattern, data['email']):
        return make_response(jsonify({'message': 'Invalid email format'}), 400)
    

 
    if User.query.filter_by(username=data['username']).first():
        return make_response(jsonify({'message': 'Username already exists'}), 400)
 
    if User.query.filter_by(email=data['email']).first():
        return make_response(jsonify({'message': 'Email already exists'}), 400)
 
    hashed_password = hashpw(data['password'].encode('utf-8'), gensalt())
    new_user = User(username=data['username'], password=hashed_password.decode('utf-8'), email=data['email'], jwt_token=None)
 
    db.session.add(new_user)
    db.session.commit()
 
    return make_response(jsonify({'message': 'Account created successfully'}), 201)
 
# Endpoint per il login e la generazione del token JWT
@app.route('/authentication/auth', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
    
    # Regex per validare lo username
    username_pattern = r'^[a-zA-Z0-9_.-]{3,20}$'
    if not re.match(username_pattern, data['username']):
        return make_response(jsonify({'message': 'Invalid username format. Only alphanumeric characters, underscores, dots, and hyphens are allowed. Length must be between 3 and 20.'}), 400)
    
 
    user = User.query.filter_by(username=data['username']).first()
    if user and checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        token = generate_jwt(user)
        # Add Token to User
        user.jwt_token = token
        db.session.commit()
        return make_response(jsonify({'message': 'Login successful', 'token': token, 'userId': user.id}), 200)
 
    return make_response(jsonify({'message': 'Invalid credentials'}), 401)
 
 # Endpoint per il Logout di un User

@app.route('/authentication/logout', methods=['PATCH'])
@token_required
def logout(current_user, token):
    account_id = request.args.get('accountId')
    if not account_id:
        return make_response(jsonify({'message': 'Account ID is required'}), 400)
 
    # Find the user by ID and clear the jwt_token field
    user = User.query.get(account_id)
    if not user:
        return make_response(jsonify({'message': 'User not found'}), 404)
 
    # Remove the Session JWT Token
    user.jwt_token = None 
    db.session.commit()
    return make_response(jsonify({'message': 'Logout successful', 'userId': user.id}), 200)
 
@app.route('/authentication/account', methods=['DELETE'])
@token_required
def delete_account(current_user, token):
    account_id = request.args.get('accountId')
    if not account_id:
        return make_response(jsonify({'message': 'Account ID is required'}), 400)
 
    # Verifica se l'utente esiste nel database
    user = User.query.get(account_id)
    if not user:
        return make_response(jsonify({'message': 'Account not found'}), 404)
 
    try:
        # Effettuare una richiesta DELETE al servizio gacha_service per eliminare la gacha collection dell'utente
        headers = {'x-access-token': token}  # Aggiungi il token all'header
        try:
            gacha_response = requests.delete(f"{GACHA_SERVICE_URL}/gacha_service/players/{account_id}/gachas", headers=headers,verify= False,timeout=5)
 
            # Controlla la risposta del gacha_service
            if gacha_response.status_code != 200 and gacha_response.status_code != 404:
                return make_response(jsonify({'message': 'Failed to delete Gacha collection from gacha_service'}), 500)
            
        except Timeout:
            return make_response(jsonify({'message': 'Failed to retrieve user information from authentication service'}), 500)
    
            
        
 
        # Cancellare l'account utente
        db.session.delete(user)
        db.session.commit()
 
        return make_response(jsonify({'message': 'Account and associated Gacha collection deleted successfully'}), 200)
 
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the gacha service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
 
@app.route('/authentication/account', methods=['PATCH'])
@token_required
def update_account(current_user, token):
    account_id = request.args.get('accountId')
    if not account_id:
        return make_response(jsonify({'message': 'Account ID is required'}), 400)
 
    user = User.query.get(account_id)
    if not user:
        return make_response(jsonify({'message': 'Account not found'}), 404)
 
    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    if 'username' in data:
        if User.query.filter_by(username=data['username']).first():
            return make_response(jsonify({'message': 'Username already exists'}), 400)
        user.username = data['username']
 
    if 'password' in data:
        hashed_password = hashpw(data['password'].encode('utf-8'), gensalt())
        user.password = hashed_password.decode('utf-8')
 
    if 'email' in data:
        if User.query.filter_by(email=data['email']).first():
            return make_response(jsonify({'message': 'Email already exists'}), 400)
        user.email = data['email']
 
    db.session.commit()
    return make_response(jsonify({'message': 'Account updated successfully'}), 200)
 
@app.route('/authentication/userId', methods=['GET'])
@token_required
def get_user_id(current_user, token):
    username = request.args.get('username')
 
    if not username:
        return make_response(jsonify({'message': 'Username is required'}), 400)
 
    user = User.query.filter_by(username=username).first()
    if not user:
        return make_response(jsonify({'message': 'User not found'}), 404)
 
    return jsonify({'userId': user.id}), 200
  
@app.route('/authentication/players/<playerId>', methods=['GET'])
@token_required
def get_user_info(current_user, token, playerId):
    try:
        # Recuperare l'utente dal database in base al playerId
        user = User.query.filter_by(id=playerId).first()

        if not user:
            return make_response(jsonify({'message': 'Player not found'}), 404)

        # Restituire tutte le informazioni dell'utente
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'wallet': user.wallet
        }

        return make_response(jsonify(user_info), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An error occurred: {str(e)}'}), 500)
    
@app.route('/authentication/players/<playerId>/currency/add', methods=['POST'])
@token_required
def add_currency_to_player(current_user, token, playerId):
    """
    Aggiunge monete di gioco al wallet del giocatore specificato
    """
    '''# Check if the Token UserId matches (PlayerID)
    # 403: Forbidden
    if (current_user.id != int(playerId)): 
        return make_response(jsonify({
    'message': 'PlayerID Invalid. You are not authorized.',
    'playerID': playerId,  # Example additional field
    'currUserID': current_user.id   # Another example additional field
}), 403)'''
 
    try:
        # Ottieni l'importo specificato dall'utente tramite la query string
        amount = request.args.get('amount', type=int)
 
        # Validare l'importo specificato
        if amount is None or amount <= 0:
            return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)
 
        # Recuperare l'utente dal database in base al playerId
        user = User.query.filter_by(id=playerId).first()
 
        if not user:
            return make_response(jsonify({'message': 'Player not found'}), 404)
 
        # Aggiungi l'importo specificato al wallet dell'utente
        user.wallet += amount
        db.session.commit()
 
        return make_response(jsonify({'message': 'Currency added successfully', 'new_wallet_balance': user.wallet}), 200)
 
    except Exception as e:
        return make_response(jsonify({'message': f'An error occurred: {str(e)}'}), 500)
 
@app.route('/authentication/players/<playerId>/currency/subtract', methods=['PATCH'])
@token_required
def subtract_currency_from_player(current_user, token, playerId):
    """
    Sottrae monete di gioco dal wallet del giocatore specificato
    """
 
    try:
        # Ottenere l'importo dal corpo della richiesta
        data = request.get_json()
        if not data or 'amount' not in data:
            return make_response(jsonify({'message': 'Invalid input data: "amount" field is required'}), 400)
 
        amount = data['amount']
 
        # Validare che l'importo sia positivo
        if amount <= 0:
            return make_response(jsonify({'message': 'Amount must be greater than zero'}), 400)
 
        # Recuperare l'utente dal database in base al playerId
        user = User.query.filter_by(id=playerId).first()
 
        if not user:
            return make_response(jsonify({'message': 'Player not found'}), 404)
 
        # Verifica se l'utente ha abbastanza currency per sottrazioni
        if user.wallet < amount:
            return make_response(jsonify({'message': 'Insufficient funds'}), 400)
 
        # Sottrarre l'importo dal wallet dell'utente
        user.wallet -= amount
        db.session.commit()
 
        return make_response(jsonify({'message': 'Wallet updated successfully', 'new_wallet_balance': user.wallet}), 200)
 
    except Exception as e:
        return make_response(jsonify({'message': f'An error occurred: {str(e)}'}), 500)
 
@app.route('/authentication/players/<playerId>/currency/update', methods=['PATCH'])
@token_required
def update_user_currency(current_user, token, playerId):
    """
    Aggiorna la quantità di currency nel wallet di un utente specifico.
    """
    # -- (!) --- questa funzione viene usata quando auctionservice dever rimborsare un utente.
 
    try:
        # Ottieni l'importo dal corpo della richiesta
        data = request.get_json()
        if not data or 'amount' not in data:
            return make_response(jsonify({'message': 'Invalid input data: "amount" field is required'}), 400)
 
        amount = data['amount']
 
        # Recuperare l'utente dal database in base al playerId
        user = User.query.filter_by(id=playerId).first()
 
        if not user:
            return make_response(jsonify({'message': 'Player not found'}), 404)
 
        # Verifica se l'utente ha abbastanza currency per sottrazioni
        if user.wallet + amount < 0:
            return make_response(jsonify({'message': 'Insufficient funds'}), 400)
 
        # Aggiorna il wallet dell'utente
        user.wallet += amount
        db.session.commit()
 
        return make_response(jsonify({'message': 'Wallet updated successfully', 'new_wallet_balance': user.wallet}), 200)
 
    except Exception as e:
        return make_response(jsonify({'message': f'An error occurred: {str(e)}'}), 500)
 
# Punto di ingresso dell'app
if __name__ == '__main__':
    app.run()