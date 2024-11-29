from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, gensalt, checkpw
import requests
from datetime import datetime, timezone, timedelta
import jwt
from functools import wraps
 
# Configura l'app Flask
app = Flask(__name__)
 
# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/users.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
 
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
 
# Decoratore per proteggere gli endpoint
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')  # Il token deve essere inviato nell'header della richiesta
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if current_user is None:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, token, *args, **kwargs)  # Passa il current_user e il token come argomento
    return decorated
 
# Definizione del modello User
class User(db.Model):
    tablename = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    wallet = db.Column(db.Integer, nullable=False, default=0)
 
    def repr(self):
        return f'<User {self.username}>'
 
# Crea il database se non esiste
with app.app_context():
    db.create_all()
 
GACHA_SERVICE_URL = 'http://gacha_service:5000'
 
# Definizione degli endpoint
 
@app.route('/authentication/account', methods=['POST'])
def create_account():
    data = request.json
    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    if User.query.filter_by(username=data['username']).first():
        return make_response(jsonify({'message': 'Username already exists'}), 400)
 
    if User.query.filter_by(email=data['email']).first():
        return make_response(jsonify({'message': 'Email already exists'}), 400)
 
    hashed_password = hashpw(data['password'].encode('utf-8'), gensalt())
    new_user = User(username=data['username'], password=hashed_password.decode('utf-8'), email=data['email'])
 
    db.session.add(new_user)
    db.session.commit()
 
    return make_response(jsonify({'message': 'Account created successfully'}), 201)
 
 
# Endpoint per il login e la generazione del token JWT
@app.route('/authentication/auth', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    user = User.query.filter_by(username=data['username']).first()
    if user and checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        token = generate_jwt(user)
        return make_response(jsonify({'message': 'Login successful', 'token': token, 'userId': user.id}), 200)
 
    return make_response(jsonify({'message': 'Invalid credentials'}), 401)
 
 
@app.route('/authentication/account', methods=['DELETE'])
@token_required
def delete_account(current_user, token):
    account_id = request.args.get('accountId')
    if not account_id:
        return make_response(jsonify({'message': 'Account ID is required'}), 400)

    # Check if the Token UserId matches the one received (AccountID)
    # 403: Forbidden
    if (current_user.id != int(account_id)): 
        return make_response(jsonify({
    'message': 'PlayerID Invalid. You are not authorized.',
    'accountID': account_id,  # Example additional field
    'currUserID': current_user.id   # Another example additional field
}), 403)
 
    # Verifica se l'utente esiste nel database
    user = User.query.get(account_id)
    if not user:
        return make_response(jsonify({'message': 'Account not found'}), 404)
 
    try:
        # Effettuare una richiesta DELETE al servizio gacha_service per eliminare la gacha collection dell'utente
        headers = {'x-access-token': token}  # Aggiungi il token all'header
        gacha_response = requests.delete(f"{GACHA_SERVICE_URL}/gacha_service/players/{account_id}/gachas", headers=headers)
 
        # Controlla la risposta del gacha_service
        if gacha_response.status_code != 200 and gacha_response.status_code != 404:
            return make_response(jsonify({'message': 'Failed to delete Gacha collection from gacha_service'}), 500)
 
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
    
    # Check if the Token UserId matches (AccountID)
    # 403: Forbidden
    if (current_user.id != int(account_id)): 
        return make_response(jsonify({'message': 'AccountID Invalid. You are not authorized.'}), 403)
 
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
    
    # Check if the Token UserId matches (user.id)
    # 403: Forbidden
    if (current_user.id != user.id): 
        return make_response(jsonify({'message': 'UserID Invalid. You are not authorized.'}), 403)
 
    return jsonify({'userId': user.id}), 200
 
 
@app.route('/authentication/players/<playerId>', methods=['GET'])
@token_required
def get_user_info(current_user, token, playerId):
    # Check if the Token UserId matches (PlayerID)
    # 403: Forbidden
    if (current_user.id != int(playerId)): 
        return make_response(jsonify({'message': 'PlayerID Invalid. You are not authorized.'}), 403)
    
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
    # Check if the Token UserId matches (PlayerID)
    # 403: Forbidden
    if (current_user.id != int(playerId)): 
        return make_response(jsonify({
    'message': 'PlayerID Invalid. You are not authorized.',
    'playerID': playerId,  # Example additional field
    'currUserID': current_user.id   # Another example additional field
}), 403)
    
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
    # Check if the Token UserId matches (PlayerID)
    # 403: Forbidden
    if (current_user.id != int(playerId)): 
        return make_response(jsonify({'message': 'PlayerID Invalid. You are not authorized.'}), 403)
    
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
def update_user_currency(current_user,token, playerId):
    """
    Aggiorna la quantità di currency nel wallet di un utente specifico.
    """
    # Check if the Token UserId matches (PlayerID)
    # 403: Forbidden
    #if (current_user.id != int(playerId)): 
    #    return make_response(jsonify({'message': 'PlayerID Invalid. You are not authorized.'}), 403)

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
    app.run(debug=True)