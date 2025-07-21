from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    app.config['SECRET_KEY'] = 'DontTellAnyone'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:01062004@localhost:5432/popmart_demo'
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .routes.views import views
    from .routes.auth import auth
    from .routes.admin import admin_bp

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .models.user import User, UserAddress
    from .models.product import Product, Collection, ProductCollection, ProductImage, InventoryLog, Wishlist
    from .models.order import Order, OrderItem, Cart, PaymentTransaction, Discount, Review, Notification

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html')
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    create_database(app)

    return app

def create_database(app):
    with app.app_context():
        db.create_all()
        print('Created Database!')