from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Mock database per gli admin
MOCK_ADMINS = {
    1: {
        "username": "admin",
        "password": "hashed_password_example",  # Mock password hash
        "jwt_token": None
    }
}

 # Mock database per gli utenti
MOCK_USERS = {
    "1": {
        "id": 1,
        "username": "player1",
        "wallet": 500,
        "email": "player1@example.com",
        "level": 10,
        "collection": [{"gacha_id": 101, "name": "Gacha A"}]
    },
    "2": {
        "id": 2,
        "username": "player2",
        "wallet": 300,
        "email": "player2@example.com",
        "level": 5,
        "collection": [{"gacha_id": 102, "name": "Gacha B"}]
    }
}

# Mock database per il catalogo e il mercato dei Gacha
MOCK_GACHAS = [
    {"gacha_id": 101, "name": "Gacha A", "rarity": "Rare", "price": 100, "market": True},
    {"gacha_id": 102, "name": "Gacha B", "rarity": "Epic", "price": 200, "market": True},
    {"gacha_id": 103, "name": "Gacha C", "rarity": "Legendary", "price": 300, "market": False}
]

# Mock database per le transazioni
MOCK_TRANSACTIONS = {
    1: [
        {"transaction_id": "tx101", "gacha_id": 101, "amount": 100, "date": "2024-11-01T10:00:00Z"},
        {"transaction_id": "tx102", "gacha_id": 102, "amount": 200, "date": "2024-11-02T12:00:00Z"}
    ],
    2: [
        {"transaction_id": "tx201", "gacha_id": 103, "amount": 150, "date": "2024-11-03T14:00:00Z"}
    ]
}


# Mock funzione per verificare la password (simula bcrypt)
def mock_checkpw(provided_password, stored_password):
    # In un test reale, puoi sostituire questa funzione con una libreria di hash come bcrypt
    return provided_password == "admin" and stored_password == "hashed_password_example"

# Mock funzione per generare un JWT
def mock_generate_jwt(admin_id):
    # Un token JWT simulato
    return f"mocked_jwt_token_for_admin_{admin_id}"

# Mock decoratore per il controllo del token
def mock_token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        # Verifica se il token è valido e associato a un admin
        for admin_id, admin_data in MOCK_ADMINS.items():
            if admin_data.get("jwt_token") == token:
                return f(current_admin={"id": admin_id, **admin_data}, token=token, *args, **kwargs)
        return jsonify({'message': 'Invalid or unauthorized token!'}), 403
    return decorated

@app.route('/admin_service/auth', methods=['POST'])
def mock_admin_login():
    """
    Mock endpoint per l'autenticazione degli admin
    """
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    # Trova l'admin usando il nome utente
    admin = next((a for a in MOCK_ADMINS.values() if a["username"] == data["username"]), None)
    if admin and mock_checkpw(data['password'], admin['password']):
        # Genera il token JWT mock
        admin_id = next(key for key, value in MOCK_ADMINS.items() if value == admin)
        token = mock_generate_jwt(admin_id)
        admin['jwt_token'] = token  # Aggiorna il token nel mock database
        return make_response(jsonify({'message': 'Login successful', 'token': token}), 200)

    return make_response(jsonify({'message': 'Invalid credentials'}), 401)

@app.route('/admin_service/logout', methods=['PATCH'], endpoint='admin_logout')
@mock_token_required
def mock_logout(current_admin, token):
    """
    Mock endpoint per il logout degli admin
    """
    admin_id = request.args.get('adminId')
    if not admin_id:
        return make_response(jsonify({'message': 'Admin ID is required'}), 400)

    try:
        admin_id = int(admin_id)
    except ValueError:
        return make_response(jsonify({'message': 'Invalid Admin ID format'}), 400)

    admin = MOCK_ADMINS.get(admin_id)
    if not admin:
        return make_response(jsonify({'message': 'Admin not found'}), 404)

    # Rimuovi il token JWT dalla mock database
    admin["jwt_token"] = None
    return make_response(jsonify({'message': 'Logout successful', 'adminId': admin_id}), 200)

@app.route('/admin_service/adminId', methods=['GET'], endpoint='get_admin_id')
@mock_token_required
def mock_get_admin_id(current_admin, token):
    """
    Mock endpoint per ottenere l'ID di un admin dato il suo username
    """
    username = request.args.get('username')

    if not username:
        return make_response(jsonify({'message': 'Username is required'}), 400)

    # Cerca l'admin usando lo username
    admin = next((admin for admin in MOCK_ADMINS.values() if admin['username'] == username), None)

    if not admin:
        return make_response(jsonify({'message': 'Admin not found'}), 404)

    # Recupera l'ID associato all'admin
    admin_id = next(key for key, value in MOCK_ADMINS.items() if value == admin)

    return jsonify({'adminId': admin_id}), 200

@app.route('/admin_service/verify_admin', methods=['GET'], endpoint='verify_admin')
@mock_token_required
def mock_verify_admin(current_admin, token):
    """
    Mock endpoint per verificare se l'utente è un admin
    """
    # Verifica i parametri necessari
    if token is None or current_admin is None:
        return make_response(jsonify({'message': 'Bad Request. Something happened on Admin Token Verification.'}), 400)

    # Se @mock_token_required è passato, allora il token è valido e l'utente è un admin
    return make_response(jsonify({'message': 'Ok.'}), 200)

@app.route('/admin_service/user_info/<playerId>', methods=['GET'], endpoint='get_user_info')
@mock_token_required
def mock_get_user_info(current_admin, token, playerId):
    """
    Mock endpoint per ottenere informazioni su un utente
    """
    # Controllo esplicito che il decoratore abbia validato correttamente il token
    if not current_admin or not token:
        return make_response(jsonify({'message': 'Invalid or unauthorized token!'}), 403)

    try:
        # Simula la ricerca dell'utente nel mock database
        user_info = MOCK_USERS.get(playerId)
        if user_info:
            return make_response(jsonify(user_info), 200)
        else:
            return make_response(jsonify({'message': 'Player not found'}), 404)

    except Exception as e:
        # Gestione degli errori generici
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

@app.route('/admin_service/gachas/<gacha_id>', methods=['PATCH'], endpoint="update_gacha")
@mock_token_required
def mock_update_gacha(current_admin, token, gacha_id):
    """
    Mock endpoint per aggiornare un Gacha nel catalogo e nelle collezioni degli utenti
    """
    # Controllo esplicito che il decoratore abbia validato correttamente il token
    if not current_admin or not token:
        return make_response(jsonify({'message': 'Invalid or unauthorized token!'}), 403)

    # Controllo dati in input
    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    try:
        # Trova il Gacha nel catalogo
        gacha = next((g for g in MOCK_GACHAS if g["gacha_id"] == int(gacha_id)), None)
        if not gacha:
            return make_response(jsonify({'message': 'Gacha not found in catalog'}), 404)

        # Aggiorna il Gacha
        gacha.update(data)

        # Aggiorna le collezioni degli utenti
        for user in MOCK_USERS.values():
            for item in user["collection"]:
                if item["gacha_id"] == int(gacha_id):
                    item.update(data)

        return make_response(jsonify({'message': 'Gacha updated successfully'}), 200)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

@app.route('/admin_service/all_collections', methods=['GET'], endpoint='get_collections')
@mock_token_required
def mock_get_all_gacha_collections(current_admin, token):
    """
    Mock endpoint per ottenere tutte le collezioni Gacha presenti nel database
    """
    # Controllo esplicito che il decoratore abbia validato correttamente il token
    if not current_admin or not token:
        return make_response(jsonify({'message': 'Invalid or unauthorized token!'}), 403)
    
    try:
        # Raccogli tutte le collezioni
        collections = [
            {"user_id": user["id"], "gachas": user["collection"]}
            for user in MOCK_USERS.values()
        ]

        if not collections:
            return make_response(jsonify({'message': 'No Gacha collections found'}), 204)

        return make_response(jsonify(collections), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
    
@app.route('/admin_service/gachas', methods=['POST'], endpoint='add_gacha')
@mock_token_required
def mock_add_gacha_to_catalog(current_admin, token):
    """
    Mock endpoint per aggiungere un nuovo gacha al catalogo tramite il gacha_market_service
    """
    # Controllo esplicito che il decoratore abbia validato correttamente il token
    if not current_admin or not token:
        return make_response(jsonify({'message': 'Invalid or unauthorized token!'}), 403)

    data = request.json
    if not data or 'name' not in data or 'rarity' not in data or 'price' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    try:
        # Genera un nuovo ID per il Gacha
        new_gacha_id = max(g["gacha_id"] for g in MOCK_GACHAS) + 1
        new_gacha = {
            "gacha_id": new_gacha_id,
            "name": data["name"],
            "rarity": data["rarity"],
            "price": data["price"],
            "market": True
        }
        MOCK_GACHAS.append(new_gacha)

        return make_response(jsonify({'message': 'Gacha added successfully', 'gacha_id': new_gacha_id}), 201)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

@app.route('/admin_service/gachas/<int:gacha_id>', methods=['DELETE'], endpoint='delete_gacha')
@mock_token_required
def mock_remove_gacha_from_catalog(current_admin, token, gacha_id):
    """
    Mock endpoint per rimuovere un gacha dal catalogo
    """
    # Verifica che il token e l'admin siano validi
    if not current_admin or not token:
        return make_response(jsonify({'message': 'Invalid or unauthorized token!'}), 403)

    try:
        # Trova il Gacha nel catalogo
        gacha_to_remove = next((gacha for gacha in MOCK_GACHAS if gacha["gacha_id"] == gacha_id), None)
        if not gacha_to_remove:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)

        # Rimuovi il Gacha dal catalogo
        MOCK_GACHAS.remove(gacha_to_remove)

        # Rimuovi il Gacha dalle collezioni degli utenti
        for user in MOCK_USERS.values():
            user["collection"] = [
                item for item in user["collection"] if item["gacha_id"] != gacha_id
            ]

        # Risposta di successo
        return make_response(jsonify({'message': 'Gacha removed successfully', 'gacha_id': gacha_id}), 200)

    except Exception as e:
        # Errore generico
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

@app.route('/admin_service/transactions/<userId>', methods=['GET'], endpoint='get_transactions')
@mock_token_required
def mock_get_user_transactions(current_admin, token, userId):
    """
    Mock endpoint per ottenere lo storico delle transazioni di un utente specifico tramite il gacha_market_service
    """
    # Verifica che il token e l'admin siano validi
    if not current_admin or not token:
        return make_response(jsonify({'message': 'Invalid or unauthorized token!'}), 403)


    try:
        # Recupera le transazioni dell'utente dal mock database
        transactions = MOCK_TRANSACTIONS.get(int(userId))
        if not transactions:
            return make_response(jsonify({'message': 'No transactions found for this user'}), 404)

        # Risposta di successo con le transazioni
        return make_response(jsonify({'userId': userId, 'transactions': transactions}), 200)

    except Exception as e:
        # Gestione di errori generici
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)


if __name__ == '__main__':
    app.run(debug=True)
