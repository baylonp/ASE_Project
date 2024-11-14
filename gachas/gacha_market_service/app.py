import requests
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurazione dell'URL del servizio di autenticazione
AUTH_SERVICE_URL = 'http://authentication:5000' 

# Configurazione del database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/gacha_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inizializza SQLAlchemy
db = SQLAlchemy(app)


# Definizione del modello Pilot
class Pilot(db.Model):
    tablename = 'pilots'
    id = db.Column(db.Integer, primary_key=True)
    pilot_name = db.Column(db.String(80), nullable=False)
    rarity = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    ability = db.Column(db.String(200), nullable=False)

    def repr(self):
        return f'<Pilot {self.pilot_name}>'

# Creazione del database (se necessario) e popolazione iniziale
with app.app_context():
    db.create_all()

    # Dati dei piloti da popolare nel database al momento della creazione della tabella

    pilots_data = [
        {"pilot_name": "Max Verstappen", "rarity": "Leggendaria", "experience": 95, "ability": "Dominatore assoluto nelle situazioni di alta pressione, aggressivo e veloce"},
        {"pilot_name": "Charles Leclerc", "rarity": "Leggendaria", "experience": 92, "ability": "Eccellente nelle qualifiche e in grado di trarre il meglio dalla vettura anche in situazioni difficili"},
        {"pilot_name": "Carlos Sainz", "rarity": "Epica", "experience": 88, "ability": "Costante e metodico, specialista delle strategie di gara che lo portano a rimontare costantemente"},
        {"pilot_name": "Lando Norris", "rarity": "Epica", "experience": 87, "ability": "Competitivo in ogni situazione, eccelle nelle condizioni difficili come la pioggia"},
        {"pilot_name": "Oscar Piastri", "rarity": "Rara", "experience": 78, "ability": "Pilota emergente che mostra grande promessa e crescita nelle prestazioni"},
        {"pilot_name": "Lewis Hamilton", "rarity": "Leggendaria", "experience": 98, "ability": "Esperto in battaglie ruota a ruota e in situazioni di alta pressione, con abilità straordinarie nelle rimonte"},
        {"pilot_name": "George Russel", "rarity": "Epica", "experience": 85, "ability": "Pilota consistente, capace di estrarre grandi prestazioni anche dalle vetture meno competitive"},
        {"pilot_name": "Sergio Perez", "rarity": "Rara", "experience": 84, "ability": "Specialista nella gestione delle gomme, ottimizza la durata degli stint"},
        {"pilot_name": "Fernando Alonso", "rarity": "Leggendaria", "experience": 97, "ability": "Maestro delle strategie e delle difese, esperto nell'adattarsi alle situazioni di gara"},
        {"pilot_name": "Nico Hulkenberg", "rarity": "Rara", "experience": 80, "ability": "Consolidato nel centro gruppo, ottiene punti preziosi in ogni occasione"},
        {"pilot_name": "Lance Stroll Jr.", "rarity": "Rara", "experience": 77, "ability": "Abile nelle partenze, ottiene buone posizioni nelle prime fasi di gara"},
        {"pilot_name": "Yuki Tsunoda", "rarity": "Comune", "experience": 73, "ability": "Competitivo, ma ancora in cerca di consistenza nel lungo periodo"},
        {"pilot_name": "Alex Albon", "rarity": "Rara", "experience": 79, "ability": "Abile nelle rimonte, riesce a ottenere buoni risultati anche con vetture meno competitive"},
        {"pilot_name": "Daniel Ricciardo", "rarity": "Epica", "experience": 85, "ability": "Esperto nei sorpassi audaci, molto efficace in situazioni di duello ruota a ruota"},
        {"pilot_name": "Kevin Magnussen", "rarity": "Comune", "experience": 74, "ability": "Aggressivo nelle prime fasi della gara, sempre pronto al combattimento"},
        {"pilot_name": "Pierre Gasly", "rarity": "Epica", "experience": 82, "ability": "Capace di ottenere il massimo risultato quando la situazione lo richiede"},
        {"pilot_name": "Esteban Ocon", "rarity": "Rara", "experience": 80, "ability": "Pilota consistente, sempre in grado di ottenere punti in condizioni stabili"},
        {"pilot_name": "Valtteri Bottas", "rarity": "Epica", "experience": 86, "ability": "Capace di supportare strategie di squadra complesse, eccelle nei long run"},
        {"pilot_name": "Zhou Guanyu", "rarity": "Comune", "experience": 72, "ability": "Pilota in crescita, sempre più consistente e sicuro nelle sue performance"},
        {"pilot_name": "Franco Colapinto", "rarity": "Comune", "experience": 70, "ability": "Promessa emergente, con grandi potenzialità per il futuro"}
    ]

    # Popolamento del database con i dati dei piloti, se non già presenti
    for pilot in pilots_data:
        existing_pilot = Pilot.query.filter_by(pilot_name=pilot['pilot_name']).first()
        if not existing_pilot:
            new_pilot = Pilot(
                pilot_name=pilot['pilot_name'],
                rarity=pilot['rarity'],
                experience=pilot['experience'],
                ability=pilot['ability']
            )
            db.session.add(new_pilot)
    
    db.session.commit()



@app.route('/players/<playerId>/currency/buy', methods=['POST'])
def buy_in_game_currency(playerId):
    """
    Compra la valuta di gioco per il wallet del giocatore specificato.
    ---
    """
    try:
        # Ottenere l'importo dalla query string
        amount = request.args.get('amount', type=float)

        # Validare l'importo specificato
        if amount is None or amount <= 0:
            return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)

        # Effettuare una richiesta POST al servizio di autenticazione per aggiornare il wallet dell'utente
        response = requests.post(
            f"{AUTH_SERVICE_URL}/players/{playerId}/currency/add",
            params={'amount': amount}
        )

        # Gestire la risposta del servizio di autenticazione
        if response.status_code == 200:
            return make_response(jsonify({'message': 'In-game currency purchased successfully'}), 200)
        elif response.status_code == 404:
            return make_response(jsonify({'message': 'Player not found'}), 404)
        else:
            return make_response(jsonify({'message': 'Failed to add currency'}), response.status_code)

    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the auth service: {str(e)}'}), 500)
    except Exception as e:
        return make_response(jsonify({'message': f'An internal error occurred: {str(e)}'}), 500)

if __name__ == 'main':
    app.run(debug=True, port=5003)