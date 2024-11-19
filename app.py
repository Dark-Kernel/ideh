from flask import Flask
from config.config import Config
from modules.webapp.models.models import db
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Register blueprints (to be implemented)
    from modules.webapp.views.auth import auth_bp, create_google_blueprint
    google_bp = create_google_blueprint(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")

    from modules.webapp.views.dashboard import dashboard_bp
    from modules.webapp.views.api import api_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'tempkey.pem'))

