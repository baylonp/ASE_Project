from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from bcrypt import checkpw, gensalt, hashpw
from datetime import datetime, timezone, timedelta
import jwt
import requests
from functools import wraps
 
# Configura l'app Flask
app = Flask(__name__)
 
# Configurazione del database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
 
# Inizializza il database
db = SQLAlchemy(app)
 
# Definizione del modello Admin
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
 
# Creazione del database e aggiunta dell'account admin hardcoded
with app.app_context():
    db.create_all()
    # Admin hardcoded - username: "admin", password: "admin"
    existing_admin = Admin.query.filter_by(username='admin').first()
    if not existing_admin:
        hashed_password = hashpw('admin'.encode('utf-8'), gensalt())
        admin = Admin(username='admin', password=hashed_password.decode('utf-8'))
        db.session.add(admin)
        db.session.commit()
 
# Funzione per creare un token JWT per l'admin
def generate_jwt(admin):
    payload = {
        'admin_id': admin.id,
        'username': admin.username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=2)  # Scadenza del token in 2 ore
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token
 
# Decoratore per proteggere gli endpoint (solo admin)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_admin = Admin.query.filter_by(id=data['admin_id']).first()
            if current_admin is None:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_admin, *args, **kwargs)
    return decorated
 
# Endpoint per il login dell'admin
@app.route('/admin_service/auth', methods=['POST'])
def admin_login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return make_response(jsonify({'message': 'Invalid input data'}), 400)
 
    admin = Admin.query.filter_by(username=data['username']).first()
    if admin and checkpw(data['password'].encode('utf-8'), admin.password.encode('utf-8')):
        token = generate_jwt(admin)
        return make_response(jsonify({'message': 'Login successful', 'token': token}), 200)
 
    return make_response(jsonify({'message': 'Invalid credentials'}), 401)
 


 
# Endpoint per ottenere informazioni su un utente (richiede token)
@app.route('/admin_service/user_info/<playerId>', methods=['GET'])
@token_required
def get_user_info(current_admin, playerId):
    # Ottieni il token JWT dall'header della richiesta
    token = request.headers.get('x-access-token')
 
    # Effettua una richiesta al servizio di autenticazione per ottenere le informazioni sull'utente
    AUTH_SERVICE_URL = 'http://authentication_service:5000'
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/authentication/players/{playerId}",
                                headers={'x-access-token': token})
        if response.status_code == 200:
            return make_response(jsonify(response.json()), 200)
        elif response.status_code == 404:
            return make_response(jsonify({'message': 'Player not found'}), 404)
        else:
            return make_response(jsonify({'message': 'Failed to retrieve user information'}), response.status_code)
    except requests.exceptions.RequestException as e:
        return make_response(jsonify({'message': f'An error occurred while communicating with the authentication service: {str(e)}'}), 500)
 
# Punto di ingresso dell'app
if __name__ == '__main__':
    app.run(debug=True)