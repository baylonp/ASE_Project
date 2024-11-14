##AUTH

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, gensalt, checkpw

# Configura l'app Flask
app = Flask(__name__)

# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# Inizializza il database
db = SQLAlchemy(app)

# Definizione del modello User
class User(db.Model):
    tablename = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    wallet = db.Column(db.Integer, nullable=False, default = 0)
    
    def repr(self):
        return f'<User {self.username}>'

# Crea il database se non esiste
with app.app_context():
    db.create_all()

# Definizione degli endpoint

@app.route('/account', methods=['POST'])
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

@app.route('/auth', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
    
    user = User.query.filter_by(username=data['username']).first()
    if user and checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        session_id = str(hash(user.username + user.password))
        return make_response(jsonify({'message': 'Login successful', 'sessionId': session_id}), 200)
    
    return make_response(jsonify({'message': 'Invalid credentials'}), 401)

@app.route('/account', methods=['DELETE'])
def delete_account():
    account_id = request.args.get('accountId')
    user = User.query.get(account_id)
    if not user:
        return make_response(jsonify({'message': 'Account not found'}), 404)
    
    db.session.delete(user)
    db.session.commit()
    
    return make_response(jsonify({'message': 'Account deleted successfully'}), 200)



@app.route('/account', methods=['PATCH'])
def update_account():
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


@app.route('/userId', methods=['GET'])
def get_user_id():

    username = request.args.get('username')
    
    if not username:
        return make_response(jsonify({'message': 'Username is required'}), 400)
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return make_response(jsonify({'message': 'User not found'}), 404)
    
    return jsonify({'userId': user.id}), 200



@app.route('/players/<playerId>/currency/add', methods=['POST'])
def add_currency_to_player(playerId):
    """
    Aggiunge monete di gioco al wallet del giocatore specificato

    """
    try:
        # Ottieni l'importo specificato dall'utente tramite la query string
        amount = request.args.get('amount', type=float)

        # Validare l'importo specificato
        if amount is None or amount <= 0:
            return make_response(jsonify({'message': 'Invalid input data: amount must be greater than zero'}), 400)

        # Recuperare l'utente dal database in base al playerId
        user = User.query.filter_by(id=playerId).first()

        if not user:
            return make_response(jsonify({'message': 'Player not found'}), 404)

        # Aggiungi l'importo specificato al wallet dell'utente
        user.wallet += int(amount)  # Aggiorna il saldo del wallet dell'utente
        db.session.commit()

        return make_response(jsonify({'message': 'Currency added successfully', 'new_wallet_balance': user.wallet}), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An error occurred: {str(e)}'}), 500)


@app.route('/players/<playerId>', methods=['GET'])
def get_user_info(playerId):
  
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
            'password': user.password,  
            'wallet': user.wallet
        }

        return make_response(jsonify(user_info), 200)

    except Exception as e:
        return make_response(jsonify({'message': f'An error occurred: {str(e)}'}), 500)



# Punto di ingresso dell'app
if __name__ == 'main':
    app.run(debug=True)