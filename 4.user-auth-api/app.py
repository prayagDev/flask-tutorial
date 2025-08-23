from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, \
    jwt_required, get_jwt_identity
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=1)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=1)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(1024), unique=True, nullable=False)
    password = db.Column(db.String(1024), nullable=False)

@app.route("/register", methods=["POST"])
def register():
    request_data = request.get_json()
    username = request_data.get("username")
    password = request_data.get("password")

    if not username or not password:
        return jsonify({"detail": "username and password required"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"detail": "Username already exists"}), 400
    
    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password=hashed_pw)
    db.session.add(user)
    db.session.commit()

    return jsonify({"detail": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    request_data = request.get_json()
    user = User.query.filter_by(username=request_data.get("username")).first()

    if not user or not bcrypt.check_password_hash(user.password, request_data.get("password")):
        return jsonify({"detail": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "access": access_token,
        "refresh": refresh_token
    })

@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    print(get_jwt_identity(), "kya print aa rha h")
    user_id = get_jwt_identity()
    new_access = create_access_token(identity=user_id)
    return jsonify({"access": new_access})

@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({"id": user.id, "username": user.username})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
