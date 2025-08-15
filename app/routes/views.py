from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models.product import Product
from sqlalchemy.sql import func
import random

views = Blueprint('views', __name__)

@views.route('/')
def home():
    # Lấy 5 sản phẩm random từ database
    products = Product.query.order_by(func.random()).limit(8).all()
    return render_template('home.html', products=products)

@views.route('/products')
def products():
    # Lấy tất cả sản phẩm từ database
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@views.route('/new-arrivals')
def new_arrivals():
    return render_template('new-arrivals.html', user=current_user)


@views.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)