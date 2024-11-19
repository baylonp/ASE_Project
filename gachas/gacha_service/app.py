from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/issuedANDownedDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definizione del modello GachaCollection
class GachaCollection(db.Model):
    tablename = 'gacha_collection'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    gacha_id = db.Column(db.Integer, nullable=False)
    pilot_name = db.Column(db.String, nullable=False)
    rarity = db.Column(db.String, nullable=False)
    experience = db.Column(db.String, nullable=False)
    ability = db.Column(db.String, nullable=False)


# Creazione del database
with app.app_context():
    db.create_all()

@app.route('/gacha_service/players/<userID>/gachas', methods=['GET'])
def get_player_gachas(userID):
    """
    Restituisce la collezione di gachas di un giocatore specifico
    """
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

@app.route('/gacha_service/players/<userID>/gachas/<gachaId>', methods=['GET'])
def get_specific_gacha(userID, gachaId):
    """
    Restituisce i dettagli di un gacha specifico della collezione di un giocatore
    """
    gacha = GachaCollection.query.filter_by(user_id=userID, gacha_id=gachaId).first()
    if not gacha:
        return make_response(jsonify({'message': 'Gacha or player not found'}), 404)

    result = {
        'gachaId': gacha.gacha_id,
        'pilotName': gacha.pilot_name,
        'rarity': gacha.rarity,
        'experience': gacha.experience,
        'ability': gacha.ability
    }

    return jsonify(result), 200

@app.route('/gacha_service/players/<userID>/gachas', methods=['POST'])
def add_gacha_to_player(userID):
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


GACHA_MARKET_SERVICE_URL = 'http://gacha_market_service:5000/catalog' 

@app.route('/gacha_service/players/<userID>/gachas/missing', methods=['GET'])
def get_missing_gachas(userID):
    """
    Restituisce i gachas mancanti dalla collezione di un giocatore rispetto al catalogo completo
    ---
    """
    try:
        # Recuperare la collezione di gachas dell'utente
        user_gachas = GachaCollection.query.filter_by(user_id=userID).all()
        user_gacha_ids = {gacha.gacha_id for gacha in user_gachas}

        # Effettuare una richiesta al servizio gacha_market_service per ottenere il catalogo completo dei gachas
        response = requests.get(f"{GACHA_MARKET_SERVICE_URL}")

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
def update_gacha_owner(userID, gachaID):
    """
    Aggiorna l'user_id del gacha specificato nella collezione dell'utente
    ---
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
    
    


if __name__ == 'main':
    app.run(debug=True)