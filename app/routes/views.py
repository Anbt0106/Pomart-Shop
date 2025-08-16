from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models.product import Product, Collection
from sqlalchemy.sql import func
import random
from .form import AddToCartForm

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

@views.route('/product/<int:product_id>')
def product_detail(product_id):
    # Lấy thông tin sản phẩm theo ID
    product = Product.query.get_or_404(product_id)
    form = AddToCartForm()
    
    # Lấy related products (cùng collection hoặc random)
    related_products = []
    if product.collections:
        # Lấy sản phẩm cùng collection
        for collection in product.collections:
            collection_products = Product.query.filter(
                Product.collections.any(id=collection.id),
                Product.id != product.id,
                Product.is_active == True
            ).limit(4).all()
            related_products.extend(collection_products)
    
    # Nếu không đủ related products, lấy thêm random
    if len(related_products) < 4:
        remaining_count = 4 - len(related_products)
        existing_ids = [p.id for p in related_products] + [product.id]
        random_products = Product.query.filter(
            ~Product.id.in_(existing_ids),
            Product.is_active == True
        ).order_by(func.random()).limit(remaining_count).all()
        related_products.extend(random_products)
    
    # Giới hạn tối đa 4 sản phẩm
    related_products = related_products[:4]
    
    return render_template('product_detail.html', product=product, form=form, related_products=related_products)

@views.route('/new-arrivals')
def new_arrivals():
    return render_template('new-arrivals.html', user=current_user)


@views.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

@views.route('/collection/<int:collection_id>')
def collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    return render_template('collection.html', collection=collection)
