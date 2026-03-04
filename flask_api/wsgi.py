from flask_server import app
from sys import exit
import os
import ssl
import logging
import sys

if __name__ == '__main__':
    context = None

    if app.config['HTTPS_ENABLED'] == 1:
        print("HTTPS Enabled")
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

    app.run(host=app.config['FLASK_RUN_HOST'], 
            port=app.config['FLASK_RUN_PORT'], 
            ssl_context=context, 
            threaded=True,
            debug=app.config['FLASK_DEBUG'])
    
# We check if we are running directly or not
if __name__ != '__main__':
    app.logger.addHandler(logging.StreamHandler(sys.stdout))



# # app.py (Logic Terraform cannot do)
# from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from models.freight_db_models import *

# app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_PATH'] = os.environ.get('DATABASE_URL')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# db = SQLAlchemy(app)

# # Create tables if they don't exist
# with app.app_context():
#     db.create_all()

# # --- CRUD ROUTES ---

# @app.route('/users', methods=['POST'])
# def create_user():
#     data = request.get_json()
#     new_user = User(name=data['name'], email=data['email'])
#     db.session.add(new_user)
#     db.session.commit() # This triggers Debezium CDC
#     return jsonify({"message": "User created", "id": new_user.id}), 201

# @app.route('/users', methods=['GET'])
# def get_users():
#     users = User.query.all()
#     return jsonify([{"id": u.id, "name": u.name, "email": u.email} for u in users])

# @app.route('/users/<int:id>', methods=['PUT'])
# def update_user(id):
#     user = User.query.get_or_404(id)
#     data = request.get_json()
#     user.name = data.get('name', user.name)
#     user.email = data.get('email', user.email)
#     db.session.commit() # Triggers an 'u' (update) event in Redpanda
#     return jsonify({"message": "User updated"})

# @app.route('/users/<int:id>', methods=['DELETE'])
# def delete_user(id):
#     user = User.query.get_or_404(id)
#     db.session.delete(user)
#     db.session.commit() # Triggers a 'd' (delete) event in Redpanda
#     return jsonify({"message": "User deleted"})

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)