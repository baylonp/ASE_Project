from flask import Flask, request, jsonify, make_response
import jwt
from functools import wraps


app = Flask(__name__)

# Configurazione dell'applicazione
app.config['SECRET_KEY'] = 'your_secret_key'


# Mock del database
MOCK_GACHAS = [
    {"id": 1, "user_id": 1, "gacha_id": 101, "pilot_name": "Ace Pilot", "rarity": "Rare", "experience": "500", "ability": "Speed Boost"},
    {"id": 2, "user_id": 1, "gacha_id": 102, "pilot_name": "Hero Pilot", "rarity": "Epic", "experience": "700", "ability": "Shield"},
    {"id": 3, "user_id": 2, "gacha_id": 103, "pilot_name": "Nova Pilot", "rarity": "Legendary", "experience": "1000", "ability": "Blast"},
    {"id": 4, "user_id": 3, "gacha_id": 103, "pilot_name": "Nova Pilot", "rarity": "Legendary", "experience": "1000", "ability": "Blast"}
]

# Decoratore per proteggere gli endpoint con autenticazione JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')  # Il token deve essere inviato nell'header della richiesta
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = decode_jwt(token)
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user_id, token, *args, **kwargs)  # Passa l'ID utente e il token come parametro
    return decorated

# Mock del token JWT
def decode_jwt(token):
    if token == "jwt_token_example":
        return {"user_id": 1}
    if token == "jwt_token_example2":
        return {"user_id": 2}
    raise jwt.InvalidTokenError

# Endpoint per gestire i Gacha di un utente
@app.route('/gacha_service/players/<userID>/gachas', methods=['GET', 'DELETE'])
@token_required
def handle_user_gachas(current_user_id, token, userID):
    global MOCK_GACHAS
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403

    if request.method == 'GET':
        user_gachas = [g for g in MOCK_GACHAS if g['user_id'] == int(userID)]
        if not user_gachas:
            return make_response(jsonify({'message': 'Player does not own any Gachas'}), 204)
        return jsonify(user_gachas), 200

    elif request.method == 'DELETE':
        MOCK_GACHAS = [g for g in MOCK_GACHAS if g['user_id'] != int(userID)]
        return make_response(jsonify({'message': 'Gacha collection deleted successfully'}), 200)

# Endpoint per ottenere un Gacha specifico
@app.route('/gacha_service/players/<userID>/gachas/<gachaId>', methods=['GET'])
@token_required
def get_specific_gacha(current_user_id, token, userID, gachaId):
    # Converto i parametri in interi per confrontarli con i dati
    user_id = int(userID)
    gacha_id = int(gachaId)


    if current_user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403

    gacha = next((g for g in MOCK_GACHAS if g['user_id'] == user_id and g['gacha_id'] == gacha_id), None)

    if not gacha:
        return make_response(jsonify({'message': 'Gacha or player not found'}), 404)

    return jsonify(gacha), 200


# Endpoint per aggiungere un nuovo Gacha
@app.route('/gacha_service/players/<userID>/gachas', methods=['POST'])
@token_required
def add_gacha_to_player(current_user_id, token, userID):
    global MOCK_GACHAS
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
    data = request.json
    if not data or not all(key in data for key in ['gacha_id', 'pilot_name', 'rarity', 'experience', 'ability']):
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
    new_gacha = {
        "id": len(MOCK_GACHAS) + 1,
        "user_id": int(userID),
        "gacha_id": data['gacha_id'],
        "pilot_name": data['pilot_name'],
        "rarity": data['rarity'],
        "experience": data['experience'],
        "ability": data['ability']
    }
    MOCK_GACHAS.append(new_gacha)
    return make_response(jsonify({'message': 'Gacha added successfully'}), 201)

# Endpoint per ottenere i Gacha mancanti
@app.route('/gacha_service/players/<userID>/gachas/missing', methods=['GET'])
@token_required
def get_missing_gachas(current_user_id, token, userID):
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
    catalog = [
        {"gacha_id": 101, "name": "Ace Pilot"},
        {"gacha_id": 102, "name": "Hero Pilot"},
        {"gacha_id": 103, "name": "Nova Pilot"},
        {"gacha_id": 104, "name": "Galaxy Pilot"}
    ]
    user_gacha_ids = {g['gacha_id'] for g in MOCK_GACHAS if g['user_id'] == int(userID)}
    missing_gachas = [g for g in catalog if g['gacha_id'] not in user_gacha_ids]
    return jsonify(missing_gachas), 200

# Endpoint per aggiornare il proprietario di uno specifico gacha
@app.route('/gacha_service/players/<userID>/gachas/<gachaID>/update_owner', methods=['PATCH'])
@token_required
def update_gacha_owner(current_user_id, token, userID, gachaID):
    global MOCK_GACHAS
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403

    try:
        # Recuperare il gacha specifico dalla collezione in base al gachaID
        gacha = next((g for g in MOCK_GACHAS if g['gacha_id'] == int(gachaID)), None)

        # Controllo se il gacha esiste nel database
        if not gacha:
            return make_response(jsonify({'message': 'Gacha not found'}), 404)

        # Aggiorna l'user_id del gacha
        gacha['user_id'] = int(userID)

        return make_response(jsonify({'message': 'Gacha ownership updated successfully'}), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)
    
# Endpoint per aggiornare un gacha nella collezione di tutti gli utenti
@app.route('/gacha_service/admin/update_all/<gacha_id>', methods=['PATCH'])
def update_gacha_for_all_users(gacha_id):
    global MOCK_GACHAS
    # Simulazione token admin
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401

    # Simula una chiamata al servizio admin
    if token != "admin_token_example":
        return jsonify({'message': 'Unauthorized access'}), 403

    # Validazione del body della richiesta
    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    try:
        # Recupera tutti i gacha che corrispondono al gacha_id
        gachas = [gacha for gacha in MOCK_GACHAS if gacha['gacha_id'] == int(gacha_id)]
        if not gachas:
            return make_response(jsonify({'message': 'No gacha found for given gacha_id'}), 404)

        # Aggiorna i parametri specificati per tutti i gacha trovati
        for gacha in gachas:
            if 'pilot_name' in data:
                gacha['pilot_name'] = data['pilot_name']
            if 'rarity' in data:
                gacha['rarity'] = data['rarity']
            if 'experience' in data:
                gacha['experience'] = data['experience']
            if 'ability' in data:
                gacha['ability'] = data['ability']

        return make_response(jsonify({'message': 'Gacha updated for all users successfully'}), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

@app.route('/gacha_service/admin/collections', methods=['GET'])
def get_all_collections():
    """
    Permette ad un admin di vedere tutto il database di Gacha Collection
    """
    try:
        # Simulazione token admin
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        # Simula richiesta all'admin_service
        if token != "admin_token_example":
            return jsonify({'message': 'Unauthorized access'}), 403

        # Recupera tutte le collezioni di Gacha
        if not MOCK_GACHAS:
            return make_response(jsonify({'message': 'No Gacha collections found'}), 204)

        # Prepara la risposta contenente tutte le collezioni di Gacha
        result = []
        for gacha in MOCK_GACHAS:
            result.append({
                'id': gacha['id'],
                'user_id': gacha['user_id'],
                'gacha_id': gacha['gacha_id'],
                'pilot_name': gacha['pilot_name'],
                'rarity': gacha['rarity'],
                'experience': gacha['experience'],
                'ability': gacha['ability']
            })

        return jsonify(result), 200

    except Exception as e:
        # Gestione di eventuali errori interni
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

# Punto di ingresso dell'app
if __name__ == '__main__':
    app.run(debug=True)
