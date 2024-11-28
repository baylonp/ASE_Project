from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import requests
import jwt
from functools import wraps
 
app = Flask(__name__)
 
# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/issuedANDownedDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
 
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
 
GACHA_MARKET_SERVICE_URL = 'http://gacha_market_service:5000/market_service/catalog'
 
@app.route('/gacha_service/players/<userID>/gachas', methods=['GET', 'DELETE'])
@token_required
def handle_user_gachas(current_user_id, token, userID):
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
 
    if request.method == 'GET':
        # Esistente: restituisce la collezione di gachas di un giocatore specifico
        gachas = GachaCollection.query.filter_by(user_id=userID).all()
        if not gachas:
            return make_response(jsonify({'message': 'Player not found'}), 404)
 
        result = []
        for gacha in gachas:
            result.append({
                'gachaId': gacha.gacha_id,
                'name': gacha.pilot_name,
                'rarity': gacha.rarity
            })
 
        return jsonify(result), 200
 
    elif request.method == 'DELETE':
        # Nuovo: elimina tutti i gacha associati a un utente specifico
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
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
 
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
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
 
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
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
 
    try:
        # Recuperare la collezione di gachas dell'utente
        user_gachas = GachaCollection.query.filter_by(user_id=userID).all()
        user_gacha_ids = {gacha.gacha_id for gacha in user_gachas}
 
        # Effettuare una richiesta al servizio gacha_market_service per ottenere il catalogo completo dei gachas
        headers = {'x-access-token': token}  # Aggiungi il token all'header
        response = requests.get(f"{GACHA_MARKET_SERVICE_URL}", headers=headers)
 
        if response.status_code != 200:
            return make_response(jsonify({'message': 'Failed to retrieve the gacha catalog from gacha_market_service'}), 500)
 
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
    if str(current_user_id) != userID:
        return jsonify({'message': 'Unauthorized access'}), 403
    
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
 
if __name__ == '__main__':
    app.run(debug=True)