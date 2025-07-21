# app/routes/admin.py
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import func

from app import db
from app.models import Product, User, Order
from app.routes.form import ShopItemForm
from app.models import Collection
from app.models import ProductImage


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Config for uploading files
UPLOAD_FOLDER = 'app/static/img/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@admin_bp.route('/')
def dashboard():
    total_products = Product.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count() if hasattr(Order, 'query') else 0
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0 if hasattr(Order, 'total_amount') else 0

    return render_template('admin/admin.html',
                         total_products=total_products,
                         total_users=total_users,
                         total_orders=total_orders,
                         total_revenue=total_revenue)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/product/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    form = ShopItemForm()
    if form.validate_on_submit():
        try:
            img = None
            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    img = f"{timestamp}_{filename}"
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, img))
                else:
                    flash('Invalid file type. Allowed types are png, jpg, jpeg, gif.', category='error')
                    return render_template('admin/add_product.html', form=form)

            # Tạo sản phẩm mới (chỉ truyền các trường có trong model)
            new_item = Product(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                stock=form.stock.data,
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                date_released=form.date_released.data
            )

            # Gán collection nếu có
            collection_name = form.collection.data
            if collection_name:
                collection_obj = Collection.query.filter_by(name=collection_name).first()
                if collection_obj:
                    new_item.collections.append(collection_obj)
                else:
                    flash('Collection not found.', category='error')
                    return render_template('admin/add_product.html', form=form)

            db.session.add(new_item)
            db.session.commit()

            # Thêm ảnh nếu có
            if img:
                product_image = ProductImage(
                    product_id=new_item.id,
                    image_url=img
                )
                db.session.add(product_image)
                db.session.commit()

            flash('Item added successfully!', category='success')
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', category='error')

    return render_template('admin/add_product.html', form=form)


@admin_bp.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_item(product_id):
    item = Product.query.get_or_404(product_id)
    form = ShopItemForm(obj=item)

    if form.validate_on_submit():
        try:
            # Cập nhật các trường cơ bản
            item.name = form.name.data
            item.description = form.description.data
            item.price = form.price.data
            item.stock = form.stock.data
            item.is_active = form.is_active.data
            item.is_featured = form.is_featured.data
            item.date_released = form.date_released.data

            # Cập nhật collection
            collection_name = form.collection.data
            if collection_name:
                collection_obj = Collection.query.filter_by(name=collection_name).first()
                if collection_obj:
                    item.collections = [collection_obj]
                else:
                    item.collections = []
            else:
                item.collections = []

            # Cập nhật ảnh sản phẩm
            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    img = f"{timestamp}_{filename}"
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, img))

                    # Xóa ảnh cũ
                    from app.models import ProductImage
                    old_images = ProductImage.query.filter_by(product_id=item.id).all()
                    for old_img in old_images:
                        old_path = os.path.join(UPLOAD_FOLDER, old_img.image_url)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                        db.session.delete(old_img)

                    # Thêm ảnh mới
                    product_image = ProductImage(
                        product_id=item.id,
                        image_url=img
                    )
                    db.session.add(product_image)

            db.session.commit()
            flash('Item edited successfully!', category='success')
            return redirect(url_for('admin.manage_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error editing item: {str(e)}', category='error')

    return render_template('admin/edit_product.html', form=form, item=item)


@admin_bp.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_item(product_id):
    item = Product.query.get_or_404(product_id)

    try:
        from app.models import ProductImage
        images = ProductImage.query.filter_by(product_id=item.id).all()
        for img in images:
            image_path = os.path.join(UPLOAD_FOLDER, img.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
            db.session.delete(img)

        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', category='success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', category='error')

    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/products', methods=['GET'])
@login_required
def manage_products():
    search_query = request.args.get('search', '').strip()
    filter_status = request.args.get('status', '').strip()

    # Query sản phẩm từ database
    query = Product.query

    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    if filter_status == 'active':
        query = query.filter(Product.is_active == True)
    elif filter_status == 'inactive':
        query = query.filter(Product.is_active == False)

    products = query.all()

    return render_template('admin/manage_products.html', products=products)