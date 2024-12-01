from flask import Flask, request, jsonify, make_response
from functools import wraps
import random
from datetime import datetime


app = Flask(__name__)

# Configurazione segreta simulata
app.config['SECRET_KEY'] = 'your_secret_key'

# Mock del database
MOCK_PILOTS = [
    {"id": 1, "pilot_name": "Max Verstappen", "rarity": "Leggendaria", "experience": 95, "ability": "Dominatore assoluto"},
    {"id": 2, "pilot_name": "Charles Leclerc", "rarity": "Leggendaria", "experience": 92, "ability": "Eccellente nelle qualifiche"},
    {"id": 3, "pilot_name": "Carlos Sainz", "rarity": "Epica", "experience": 88, "ability": "Specialista strategie"},
    {"id": 4, "pilot_name": "Oscar Piastri", "rarity": "Rara", "experience": 78, "ability": "Promessa emergente"}
]

# Mock del database delle transazioni
MOCK_TRANSACTIONS = [
    {"id": 1, "user_id": "1", "amount_spent": 50.0, "timestamp": "2024-11-28T10:00:00+00:00"},
    {"id": 2, "user_id": "1", "amount_spent": 20.0, "timestamp": "2024-11-29T12:30:00+00:00"},
    {"id": 3, "user_id": "2", "amount_spent": 100.0, "timestamp": "2024-11-30T15:45:00+00:00"},
]

MOCK_USERS = {"1": {"wallet": 500}, "2": {"wallet": 300}}  # Mock del portafoglio dell'utente

# Simulazione del token admin
ADMIN_TOKEN = "admin_token_example"
# Simulazione token
USER_TOKEN = "jwt_token_example"

# Decoratore mock per autenticazione
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token or token != USER_TOKEN:
            return jsonify({'message': 'Token is invalid or missing!'}), 401
        current_user_id = 1  # Utente mock con ID 1
        return f(current_user_id, token, *args, **kwargs)
    return decorated

# Simulazione dell'admin. Aggiornamento del pilota nel mock database.
@app.route('/market_service/admin/gachas/<gacha_id>', methods=['PATCH'])
def update_gacha_catalog(gacha_id):
    # Verifica token admin
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    if token != ADMIN_TOKEN:
        return jsonify({'message': 'Unauthorized access'}), 403

    # Dati della richiesta
    data = request.json
    if not data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)

    # Aggiornamento del pilota nel mock database
    gacha = next((pilot for pilot in MOCK_PILOTS if pilot['id'] == int(gacha_id)), None)
    if not gacha:
        return make_response(jsonify({'message': 'Gacha not found'}), 404)

    # Aggiorna i campi forniti
    if 'pilot_name' in data:
        gacha['pilot_name'] = data['pilot_name']
    if 'rarity' in data:
        gacha['rarity'] = data['rarity']
    if 'experience' in data:
        gacha['experience'] = data['experience']
    if 'ability' in data:
        gacha['ability'] = data['ability']

    return make_response(jsonify({'message': 'Gacha updated successfully'}), 200)

# Restituisce lo storico delle transazioni per un utente specifico.
@app.route('/market_service/players/<userId>/transactions', methods=['GET'])
def get_user_transactions(userId):
    # Verifica token
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    if token != USER_TOKEN:
        return jsonify({'message': 'Unauthorized access'}), 403

    # Recupera le transazioni dal mock database
    user_transactions = [t for t in MOCK_TRANSACTIONS if t['user_id'] == userId]

    if not user_transactions:
        return make_response(jsonify({'message': 'No transactions found for this user'}), 404)

    return make_response(jsonify(user_transactions), 200)

# Compra la valuta di gioco per il wallet del giocatore specificato.
@app.route('/market_service/players/<playerId>/currency/buy', methods=['POST'])
def buy_in_game_currency(playerId):
    # Verifica token
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    if token != USER_TOKEN:
        return jsonify({'message': 'Unauthorized access'}), 403

    # Verifica se l'utente esiste
    user = MOCK_USERS.get(playerId)
    if not user:
        return make_response(jsonify({'message': 'Player not found'}), 404)

    # Recupera l'importo dall'argomento della richiesta
    amount = request.args.get('amount', type=float)
    if amount is None or amount <= 0:
        return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)

    # Aggiorna il wallet dell'utente
    try:
        user['wallet'] += amount

        # Registra la transazione
        MOCK_TRANSACTIONS.append({
            "id": len(MOCK_TRANSACTIONS) + 1,
            "user_id": playerId,
            "amount_spent": amount,
            "timestamp": datetime.now().isoformat()
        })

        return make_response(jsonify({'message': 'In-game currency purchased successfully'}), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

# Catalogo dei piloti
@app.route('/market_service/catalog', methods=['GET'])
@token_required
def get_catalog(current_user_id, token):
    if not MOCK_PILOTS:
        return make_response(jsonify({'message': 'No pilots available in the catalog'}), 404)
    return jsonify(MOCK_PILOTS), 200

# Endpoint per acquistare una roll (gacha)
@app.route('/market_service/players/<playerId>/gacha/roll', methods=['POST'])
def buy_gacha_roll(playerId):
    """
    Consente all'utente di acquistare una roll (gacha) per ottenere un pilota casuale.
    """
    # Verifica token
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    if token != USER_TOKEN:
        return jsonify({'message': 'Unauthorized access'}), 403

    # Verifica se l'utente esiste
    user = MOCK_USERS.get(playerId)
    if not user:
        return jsonify({'message': 'Player not found'}), 404

    ROLL_COST = 100  # Costo della roll

    # Controlla se l'utente ha abbastanza credito
    if user['wallet'] < ROLL_COST:
        return jsonify({'message': 'Not enough in-game currency to purchase a roll'}), 400

    # Controlla se ci sono piloti disponibili
    if not MOCK_PILOTS:
        return jsonify({'message': 'No pilots available in the catalog'}), 404

    # Esegui la roll basata sulla rarità
    def get_random_pilot(pilots):
        rarity_weights = {
            'Leggendaria': 5,
            'Epica': 10,
            'Rara': 20,
            'Comune': 65
        }
        rarities = {pilot['rarity'] for pilot in pilots}
        weights = [rarity_weights[rarity] for rarity in rarities]

        selected_rarity = random.choices(list(rarities), weights=weights, k=1)[0]
        filtered_pilots = [pilot for pilot in pilots if pilot['rarity'] == selected_rarity]
        return random.choice(filtered_pilots)

    selected_pilot = get_random_pilot(MOCK_PILOTS)

    # Deduce il costo dal wallet dell'utente
    user['wallet'] -= ROLL_COST

    # Mock della risposta per aggiungere il pilota alla collezione
    gacha_data = {
        "gacha_id": selected_pilot["id"],
        "pilot_name": selected_pilot["pilot_name"],
        "rarity": selected_pilot["rarity"],
        "experience": selected_pilot["experience"],
        "ability": selected_pilot["ability"]
    }

    # Registra la transazione
    MOCK_TRANSACTIONS.append({
        "id": len(MOCK_TRANSACTIONS) + 1,
        "user_id": playerId,
        "amount_spent": ROLL_COST,
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({
        'message': 'Roll purchased successfully',
        'pilot': gacha_data
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
