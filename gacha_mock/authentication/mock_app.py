from flask import Flask, request, jsonify, make_response
from bcrypt import hashpw, gensalt, checkpw
import requests
from datetime import datetime, timezone, timedelta
import jwt
from functools import wraps
 
# Configura l'app Flask
app = Flask(__name__)
 
# Decoratore per proteggere gli endpoint
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')  # Il token deve essere inviato nell'header della richiesta
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            decoded_token = decode_jwt(token)
            current_user = next((u for u in MOCK_USERS if u['id'] == decoded_token['user_id']), None)
            if current_user is None:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, token, *args, **kwargs)  # Passa il current_user e il token come argomento
    return decorated
 
# Mock dei dati iniziali
MOCK_USERS = [
    {"id": 1, "username": "test_user", "password": "secure_password",
     "email": "test_user@example.com", "wallet": 500},
    {"id": 2, "username": "existing_user", "password": "password_123",
     "email": "existing_email@example.com", "wallet": 300},
]

MOCK_NEXT_USER_ID = max(u['id'] for u in MOCK_USERS)

# Simula il Gacha Service
MOCK_GACHA_COLLECTIONS = {1: ["item1", "item2"]}

# Mock del tocken JWT. 
# Viene generato e validato un tocken statico coerente con i test del file JSON
def generate_jwt(username=None, user_id=None):
    if username == "test_user" and user_id == 1:
        return "jwt_token_example"
    if username == "existing_user" and user_id == 2:
        return "jwt_token_example2"
    raise jwt.InvalidTokenError("Invalid user details")



def decode_jwt(token):
    if token == "jwt_token_example":
        return {"user_id": 1, "username": "test_user"}
    if token == "jwt_token_example2":
        return {"user_id": 2, "username": "existing_user"}
    raise jwt.InvalidTokenError

 
# Definizione degli endpoint Mock

@app.route("/authentication/validate", methods=["GET"])
@token_required
def validate_service_token(curr_user, token):
    """
    Endpoint to validate JWT token.
    """
    # Verifica eventuali errori non gestiti dal decoratore @token_required
    if curr_user is None or token is None: 
        return make_response(jsonify({
            'message': 'Bad Request. Something happened on Token Verification.'
        }), 400)  # Bad Request
    
    # Se il decoratore @token_required ha validato correttamente il token
    return make_response(jsonify({
        'message': 'Ok.'
    }), 200)  # OK

 
@app.route('/authentication/account', methods=['POST'])
def create_account():
    # Dichiarazione esplicita come variabile globale
    global MOCK_NEXT_USER_ID

    data = request.json
    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    if any(u['username'] == data['username'] for u in MOCK_USERS):
        return make_response(jsonify({'message': 'Username already exists'}), 400)
 
    if any(u['email'] == data['email'] for u in MOCK_USERS):
        return make_response(jsonify({'message': 'Email already exists'}), 400)

    new_user = {
    "id": MOCK_NEXT_USER_ID + 1,
    "username": data['username'],
    "password": data['password'],  # Password salvata in chiaro
    "email": data['email'],
    "wallet": 0
    }
    MOCK_USERS.append(new_user)
    MOCK_NEXT_USER_ID += 1
 
    return make_response(jsonify({'message': 'Account created successfully'}), 201)
 
 
# Endpoint per il login e la generazione del token JWT
@app.route('/authentication/auth', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    user = next((u for u in MOCK_USERS if u['username'] == data['username']), None)
    if user and data['password'] == user['password']:
        token = generate_jwt(username=user['username'], user_id=user['id'])
        return make_response(jsonify({'message': 'Login successful', 'token': token, 'userId': user['id']}))

    return make_response(jsonify({'message': 'Invalid credentials'}), 401)



@app.route('/authentication/logout', methods=['PATCH'])
@token_required
def logout(current_user, token):
    account_id = request.args.get('accountId', type=int)
    if not account_id:
        return make_response(jsonify({'message': 'Account ID is required'}), 400)

    # Verifica che l'account ID corrisponda a quello dell'utente corrente
    if current_user['id'] != account_id:
        return make_response(jsonify({'message': 'AccountID Invalid. You are not authorized.'}), 403)

    # Simula la rimozione del token
    # In un'applicazione reale, il token sarebbe invalidato (es. rimosso da un database o blacklistato)
    return make_response(jsonify({'message': 'Logout successful', 'userId': current_user['id']}), 200)

 
 
@app.route('/authentication/account', methods=['DELETE'])
@token_required
def delete_account(current_user, token):
    # Recupera il token dal header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Recupera il parametro accountId dalla query string
    account_id = request.args.get('accountId', type=int)
    if not account_id:
        return make_response(jsonify({"message": "Account ID is required"}), 400)

    if account_id != current_user_id:
        return make_response(jsonify({
            "message": "PlayerID Invalid. You are not authorized.",
            "accountID": account_id,
            "currUserID": current_user_id
        }), 403)

    # Trova l'utente nel mock database
    user = next((u for u in MOCK_USERS if u['id'] == account_id), None)
    if not user:
        return make_response(jsonify({"message": "Account not found"}), 404)

    # Simula chiamata al Gacha Service
    try:
        if account_id in MOCK_GACHA_COLLECTIONS:
            # Simula successo della chiamata DELETE
            del MOCK_GACHA_COLLECTIONS[account_id]
        else:
            # Simula che la collezione non esista (non è un errore)
            pass
    except Exception:
        return make_response(jsonify({"message": "Failed to delete Gacha collection from gacha_service"}), 500)

    # Rimuovi l'utente dal mock database
    MOCK_USERS.remove(user)

    return make_response(jsonify({"message": "Account and associated Gacha collection deleted successfully"}), 200)
 
 
@app.route('/authentication/account', methods=['PATCH'])
@token_required
def update_account(current_user, token):
    # Recupera il token dal header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Recupera il parametro accountId dalla query string
    account_id = request.args.get('accountId', type=int)
    if not account_id:
        return make_response(jsonify({"message": "Account ID is required"}), 400)

    if account_id != current_user_id:
        return make_response(jsonify({"message": "AccountID Invalid. You are not authorized."}), 403)

    # Trova l'utente nel mock database
    user = next((u for u in MOCK_USERS if u['id'] == account_id), None)
    if not user:
        return make_response(jsonify({"message": "Account not found"}), 404)

    # Parsing del body della richiesta
    data = request.json
    if not data:
        return make_response(jsonify({"message": "Invalid input data"}), 400)

    # Aggiorna i campi richiesti
    if 'username' in data:
        if any(u['username'] == data['username'] and u['id'] != account_id for u in MOCK_USERS):
            return jsonify({"message": "Username already exists"}), 400
        user['username'] = data['username']

    if 'password' in data:
        hashed_password = hashpw(data['password'].encode('utf-8'), gensalt()).decode('utf-8')
        user['password'] = hashed_password

    if 'email' in data:
        if any(u['email'] == data['email'] and u['id'] != account_id for u in MOCK_USERS):
            return jsonify({"message": "Email already exists"}), 400
        user['email'] = data['email']

    # Simula il commit nel mock database
    return make_response(jsonify({"message": "Account updated successfully"}), 200)
 
 
 
@app.route('/authentication/userId', methods=['GET'])
@token_required
def get_user_id(current_user, token):
    # Recupera il token dall'header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Recupera il parametro 'username' dalla query string
    username = request.args.get('username')
    if not username:
        return make_response(jsonify({"message": "Username is required"}), 400)

    # Cerca l'utente per username nel mock database
    user = next((u for u in MOCK_USERS if u['username'] == username), None)
    if not user:
        return make_response(jsonify({"message": "User not found"}), 404)

    # Autorizzazione: l'utente può accedere solo al proprio username
    if user["id"] != current_user_id:
        return make_response(jsonify({"message": "UserID Invalid. You are not authorized."}), 403)

    # Restituisce l'ID dell'utente
    return make_response(jsonify({"userId": user["id"]}), 200)
 
 
@app.route('/authentication/players/<playerId>', methods=['GET'])
@token_required
def get_user_info(current_user, token, playerId):
    # Cast ad intero 
    playerId = int(playerId)
    # Recupera il token dall'header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Autorizzazione: l'utente può accedere solo al proprio playerId
    if playerId != current_user_id:
        return make_response(jsonify({"message": "PlayerID Invalid. You are not authorized."}), 403)

    # Recupera il giocatore dal mock database
    player = next((u for u in MOCK_USERS if u['id'] == playerId), None)
    if not player:
        return make_response(jsonify({"message": "Player not found"}), 404)

    # Restituisce le informazioni del giocatore
    player_info = {
        "id": player["id"],
        "username": player["username"],
        "email": player["email"],
        "wallet": player["wallet"]
    }

    return make_response(jsonify(player_info), 200)
 
 
@app.route('/authentication/players/<playerId>/currency/add', methods=['POST'])
@token_required
def add_currency_to_player(current_user, token, playerId):
    # Cast ad intero 
    playerId = int(playerId)
    # Recupera il token dall'header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Autorizzazione: l'utente può aggiungere currency solo al proprio account
    if playerId != current_user_id:
        return make_response(jsonify({
            "message": "PlayerID Invalid. You are not authorized.",
            "playerID": playerId,
            "currUserID": current_user_id
        }), 403)

    # Recupera l'importo dalla query string
    try:
        amount = int(request.args.get('amount'))
    except (TypeError, ValueError):
        return make_response(jsonify({"message": "Invalid input data: amount must be greater than zero"}), 400)

    if amount <= 0:
        return make_response(jsonify({"message": "Invalid input data: amount must be greater than zero"}), 400)

    # Cerca il giocatore nel mock database
    user = next((u for u in MOCK_USERS if u['id'] == playerId), None)
    if not user:
        return make_response(jsonify({"message": "Player not found"}), 404)

    # Aggiorna il wallet dell'utente
    user["wallet"] += amount

    # Restituisce la risposta con il nuovo saldo
    return make_response(jsonify({
        "message": "Currency added successfully",
        "new_wallet_balance": user["wallet"]
    }), 200)
 
 
@app.route('/authentication/players/<playerId>/currency/subtract', methods=['PATCH'])
@token_required
def subtract_currency_from_player(current_user, token, playerId):
    # Cast ad intero 
    playerId = int(playerId)
    # Recupera il token dall'header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Autorizzazione: l'utente può sottrarre currency solo al proprio account
    if playerId != current_user_id:
        return make_response(jsonify({
            "message": "PlayerID Invalid. You are not authorized.",
            "playerID": playerId,
            "currUserID": current_user_id
        }), 403)

    # Recupera l'importo dal corpo della richiesta
    data = request.get_json()
    if not data or 'amount' not in data:
        return make_response(jsonify({"message": "Invalid input data: \"amount\" field is required"}), 400)

    amount = data['amount']
    if not isinstance(amount, int) or amount <= 0:
        return make_response(jsonify({"message": "Invalid input data: amount must be greater than zero"}), 400)

    # Cerca il giocatore nel mock database
    user = next((u for u in MOCK_USERS if u['id'] == playerId), None)
    if not user:
        return make_response(jsonify({"message": "Player not found"}), 404)

    # Verifica se il giocatore ha abbastanza currency
    if user["wallet"] < amount:
        return make_response(jsonify({"message": "Insufficient funds"}), 400)

    # Aggiorna il wallet dell'utente
    user["wallet"] -= amount

    # Restituisce la risposta con il nuovo saldo
    return make_response(jsonify({
        "message": "Wallet updated successfully",
        "new_wallet_balance": user["wallet"]
    }), 200)
 
@app.route('/authentication/players/<playerId>/currency/update', methods=['PATCH'])
@token_required
def update_user_currency(current_user, token, playerId):
    # Cast ad intero 
    playerId = int(playerId)
    # Recupera il token dall'header
    token = request.headers.get('x-access-token')
    if not token:
        return make_response(jsonify({"message": "Token is missing"}), 401)

    try:
        decoded_token = decode_jwt(token)
    except jwt.InvalidTokenError:
        return make_response(jsonify({"message": "Invalid token"}), 401)

    current_user_id = decoded_token['user_id']

    # Autorizzazione: l'utente può aggiornare currency solo sul proprio account
    if playerId != current_user_id:
        return make_response(jsonify({
            "message": "PlayerID Invalid. You are not authorized.",
            "playerID": playerId,
            "currUserID": current_user_id
        }), 403)

    # Recupera l'importo dal corpo della richiesta
    data = request.get_json()
    if not data or 'amount' not in data:
        return make_response(jsonify({"message": "Invalid input data: \"amount\" field is required"}), 400)

    amount = data['amount']
    if not isinstance(amount, int):
        return make_response(jsonify({"message": "Invalid input data: \"amount\" must be an integer"}), 400)

    # Cerca il giocatore nel mock database
    user = next((u for u in MOCK_USERS if u['id'] == playerId), None)
    if not user:
        return make_response(jsonify({"message": "Player not found"}), 404)

    # Verifica che il wallet non scenda sotto zero
    if user["wallet"] + amount < 0:
        return make_response(jsonify({"message": "Insufficient funds"}), 400)

    # Aggiorna il wallet dell'utente
    user["wallet"] += amount

    # Restituisce la risposta con il nuovo saldo
    return make_response(jsonify({
        "message": "Wallet updated successfully",
        "new_wallet_balance": user["wallet"]
    }), 200)
 
# Punto di ingresso dell'app
if __name__ == '__main__':
    app.run(debug=True)