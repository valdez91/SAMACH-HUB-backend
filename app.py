from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, migrate, jwt, mail
from routes.auth import auth_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # Import models so Flask-Migrate detects them
    from models import User, OTP, Facility, AccessKey
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # Blueprints (we’ll add routes next)
    # from routes.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix="/api/auth")

    @app.route("/")
    def index():
        return {"message": "Samach-Hub API is running"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
