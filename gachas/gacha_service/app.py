from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy

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

# Definizione del modello GachaCatalog
class GachaCatalog(db.Model):
    tablename = 'gacha_catalog'
    gacha_id = db.Column(db.Integer, primary_key=True)
    pilot_name = db.Column(db.String, nullable=False)
    rarity = db.Column(db.String, nullable=False)
    experience = db.Column(db.String, nullable=False)
    ability = db.Column(db.String, nullable=False)



# Creazione del database
with app.app_context():
    db.create_all()

@app.route('/players/<userID>/gachas', methods=['GET'])
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

@app.route('/players/<userID>/gachas/<gachaId>', methods=['GET'])
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

@app.route('/players/<userID>/gachas', methods=['POST'])
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



@app.route('/players/<userID>/missing_gachas', methods=['GET'])
def get_missing_gachas(userID):
    """
    Restituisce i gachas mancanti dalla collezione di un giocatore rispetto al catalogo completo
    """
    # Trova tutti i gachas posseduti dall'utente
    user_gachas = GachaCollection.query.filter_by(user_id=userID).all()
    user_gacha_ids = {gacha.gacha_id for gacha in user_gachas}

    # Trova tutti i gachas nel catalogo
    all_gachas = GachaCatalog.query.all()

    # Filtra i gachas mancanti
    missing_gachas = [gacha for gacha in all_gachas if gacha.gacha_id not in user_gacha_ids]

    if not missing_gachas:
        return make_response(jsonify({'message': 'Player has all gachas'}), 200)

    result = []
    for gacha in missing_gachas:
        result.append({
            'gachaId': gacha.gacha_id,
            'pilotName': gacha.pilot_name,
            'rarity': gacha.rarity
        })

    return make_response(jsonify({'message': 'Missing Gachas are CAMBIATO: '}, result), 201)
    #return jsonify(result), 200


##BURNER DB INITIALIZATION- DA TOGLIERE

@app.route('/catalog/init', methods=['POST'])
def initialize_catalog():
    """
    Popola il catalogo con gachas di esempio per testare gli endpoint
    """
    sample_gachas = [
        {"gacha_id": "gacha001", "pilot_name": "Pilot Alpha", "rarity": "Rare", "experience": "0", "ability": "Speed Boost"},
        {"gacha_id": "gacha002", "pilot_name": "Pilot Beta", "rarity": "Epic", "experience": "3", "ability": "Shield"},
        {"gacha_id": "gacha003", "pilot_name": "Pilot Gamma", "rarity": "Legendary", "experience": "0", "ability": "Double Attack"},
        {"gacha_id": "gacha004", "pilot_name": "Pilot Delta", "rarity": "Common", "experience": "5", "ability": "Dodge"},
        {"gacha_id": "gacha005", "pilot_name": "Pilot Epsilon", "rarity": "Rare", "experience": "0", "ability": "Fire Strike"}
    ]

    for gacha_data in sample_gachas:
        gacha = GachaCatalog.query.filter_by(gacha_id=gacha_data["gacha_id"]).first()
        if not gacha:
            new_gacha = GachaCatalog(
                gacha_id=gacha_data["gacha_id"],
                pilot_name=gacha_data["pilot_name"],
                rarity=gacha_data["rarity"],
                experience=gacha_data["experience"],
                ability=gacha_data["ability"]
            )
            db.session.add(new_gacha)

    db.session.commit()
    return make_response(jsonify({'message': 'Catalog initialized successfully'}), 201)


if __name__ == 'main':
    app.run(debug=True)