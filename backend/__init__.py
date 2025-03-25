from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config['SECRET_KEY'] = 'secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_NAME
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'  # Lưu session vào file
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Hỗ trợ CORS
    app.config['SESSION_COOKIE_SECURE'] = True  # Dùng HTTPS nếu deploy
    app.config['UPLOAD_FOLDER'] = 'static/uploads'

    db.init_app(app)

    from .views import views
    from .auth import auth
    from .menu import menu
    from .table import table
    from .order import order
    from .models import User, MenuItem, Category, Table, Order, OrderItem

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(menu, url_prefix='/')
    app.register_blueprint(table, url_prefix='/')
    app.register_blueprint(order, url_prefix='/')

    create_db(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    return app

def create_db(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')