from flask import Flask, request, jsonify
import couchdb
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Connect to CouchDB server with authentication
couch = couchdb.Server('http://admin:admin@localhost:5984/')
db_name = 'nyanmew'
if db_name in couch:
    db = couch[db_name]
else:
    db = couch.create(db_name)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=8)

    logging.debug(f"Registering user: {username}, Hashed password: {hashed_password}")

    user = {
        '_id': username,  # Use username as the document ID
        'username': username,
        'password': hashed_password,
        'mood_logs': []
    }

    if db.get(username) is None:
        db.save(user)
        return jsonify({"message": "User registered successfully!"}), 201
    else:
        return jsonify({"message": "Username already exists!"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = db.get(username)
    if user:
        logging.debug(f"User found: {username}, Stored hashed password: {user['password']}")
        if check_password_hash(user['password'], password):
            return jsonify({"message": "Login successful!", "username": username}), 200
        else:
            logging.debug("Invalid password")
            return jsonify({"message": "Invalid password!"}), 401
    else:
        logging.debug("User not found")
        return jsonify({"message": "User not found!"}), 404

@app.route('/mood', methods=['POST'])
def log_mood():
    data = request.get_json()
    username = data['username']
    mood = data['mood']
    timestamp = datetime.utcnow().isoformat() + 'Z'  # Generating ISO 8601 formatted timestamp

    user = db.get(username)
    if user:
        mood_log = {
            'mood': mood,
            'timestamp': timestamp
        }
        user['mood_logs'].append(mood_log)
        db.save(user)
        return jsonify({"message": "Mood logged successfully!"}), 201
    else:
        return jsonify({"message": "User not found!"}), 404

@app.route('/user/<username>', methods=['GET'])
def get_user_data(username):
    user = db.get(username)
    if user:
        user_data = {
            'username': user['username'],
            'mood_logs': user['mood_logs']
        }
        return jsonify(user_data), 200
    else:
        return jsonify({"message": "User not found!"}), 404

if __name__ == '__main__':
    app.run(debug=True)
