from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, gensalt, checkpw

# Configura l'app Flask
app = Flask(__name__)

# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Usa PostgreSQL se necessario
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



# Punto di ingresso dell'app
if __name__ == 'main':
    app.run(debug=True)