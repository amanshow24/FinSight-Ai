from flask import Flask
from flask_restx import Api
import firebase_admin
from firebase_admin import credentials
from config import Config
app = Flask(__name__)
app.config.from_object(Config)
cred = credentials.Certificate(app.config["FIREBASE_CRED_PATH"])
firebase_admin.initialize_app(cred, {
    "storageBucket": app.config["STORAGE_BUCKET"]
})
print("Firebase connected!")
api = Api(
    app,
    version="1.0",
    title="FinSense AI API",
    description="AI-Powered Bank Statement Analyzer",
    doc="/docs"
)
from routes.auth_routes import auth_ns
from routes.statement_routes import stmt_ns
from flask_restx import Namespace, Resource

api.add_namespace(auth_ns,  path="/auth")
api.add_namespace(stmt_ns,  path="/statement")
health_ns = Namespace("health", description="Health check")
api.add_namespace(health_ns, path="/health")

@health_ns.route("")
class Health(Resource):
    def get(self):
        return {
            "status":   "ok",
            "message":  "FinSense AI running! ",
            "version":  "1.0.0",
            "firebase": "connected"
        }, 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
