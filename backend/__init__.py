from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, current_user
import os
from .models import db, User

DB_NAME = "database.db"

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config['SECRET_KEY'] = 'your-secret-key'  # Thay đổi key này trong môi trường production
    
    # Tạo thư mục instance nếu chưa tồn tại
    if not os.path.exists('instance'):
        os.makedirs('instance')
        
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_NAME
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'  # Lưu session vào file
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Hỗ trợ CORS
    app.config['SESSION_COOKIE_SECURE'] = True  # Dùng HTTPS nếu deploy
    app.config['UPLOAD_FOLDER'] = 'static/uploads'

    # Khởi tạo các extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Đăng ký các blueprints
    from .views import views
    from .auth import auth
    from .menu import menu
    from .table import table
    from .order import order
    from .material import material
    from .report import report


    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(menu, url_prefix='/')
    app.register_blueprint(table, url_prefix='/')
    app.register_blueprint(order, url_prefix='/')
    app.register_blueprint(material, url_prefix='/')
    app.register_blueprint(report, url_prefix='/')
    # Tạo database
    with app.app_context():
        db.create_all()
    
    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_db(app):
    if not path.exists('instance/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')