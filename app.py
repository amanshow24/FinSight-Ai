from flask import Flask
from flask_restx import Api
import firebase_admin
from firebase_admin import credentials
from config import Config
app = Flask(__name__)
app.config.from_object(Config)
api = Api(
    app,
    version="1.0",
    title="FinSense AI API",
    description="AI-Powered Bank Statement Analyzer",
    doc="/docs"
)
cred = credentials.Certificate(app.config["FIREBASE_CRED_PATH"])
firebase_admin.initialize_app(cred)
print("Firebase connected successfully!")
from flask_restx import Resource, Namespace
health_ns = Namespace("health", description="Health check")
api.add_namespace(health_ns, path="/health")

@health_ns.route("")
class HealthCheck(Resource):
    def get(self):
        """Check if API is running"""
        return {
            "status": "ok",
            "message": "FinSense AI is running!",
            "version": "1.0.0",
            "firebase": "connected"
        }, 200
if __name__ == "__main__":
    app.run(debug=True, port=5000)