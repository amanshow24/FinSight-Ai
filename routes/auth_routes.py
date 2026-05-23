from flask_restx import Namespace, Resource, fields
from flask import request
from firebase_admin import auth as firebase_auth
from services.auth_service import generate_token
from services.firebase_service import create_user, get_user

auth_ns = Namespace("auth", description="Authentication")

# ── Request Models (for Swagger docs) ──
register_model = auth_ns.model("Register", {
    "email":    fields.String(required=True, example="user@gmail.com"),
    "password": fields.String(required=True, example="password123"),
    "name":     fields.String(required=True, example="Sayan Sil"),
})

login_model = auth_ns.model("Login", {
    "email":    fields.String(required=True, example="user@gmail.com"),
    "password": fields.String(required=True, example="password123"),
})


# ════════════════════════════
#   REGISTER
# ════════════════════════════
@auth_ns.route("/register")
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        """Register a new user"""
        data = request.json
        email    = data.get("email")
        password = data.get("password")
        name     = data.get("name")

        if not email or not password or not name:
            return {"message": "Email, password and name required"}, 400

        try:
            # Create user in Firebase Auth
            user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=name
            )

            # Save to Firestore
            create_user(user.uid, email, name)

            # Generate JWT
            token = generate_token(user.uid, email)

            return {
                "message": "User registered successfully!",
                "token":   token,
                "uid":     user.uid,
                "name":    name
            }, 201

        except firebase_auth.EmailAlreadyExistsError:
            return {"message": "Email already registered!"}, 409
        except Exception as e:
            return {"message": str(e)}, 500


# ════════════════════════════
#   LOGIN
# ════════════════════════════
@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        """Login and get JWT token"""
        data  = request.json
        email = data.get("email")

        if not email:
            return {"message": "Email required"}, 400

        try:
            # Get user from Firebase
            user  = firebase_auth.get_user_by_email(email)
            token = generate_token(user.uid, email)

            # Get user data from Firestore
            user_data = get_user(user.uid)

            return {
                "message": "Login successful!",
                "token":   token,
                "uid":     user.uid,
                "name":    user_data.get("name") if user_data else ""
            }, 200

        except firebase_auth.UserNotFoundError:
            return {"message": "User not found!"}, 404
        except Exception as e:
            return {"message": str(e)}, 500