# app/routes/admin.py
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
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
    # Get all collections for the datalist
    collections = Collection.query.all()
    collection_names = [c.name for c in collections]

    if request.method == 'POST':

        if not form.validate():
            print("Form validation errors:", form.errors)  # Debug print
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Lỗi ở trường {field}: {error}', 'error')
            return render_template('admin/add_product.html', form=form, collection_names=collection_names)

    if form.validate_on_submit():
        try:
            print("Form validated successfully")  # Debug print
            # 1. Create Product instance
            new_item = Product(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                stock=form.stock.data,
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                date_released=form.date_released.data
            )

            # 2. Add product to session and flush to get ID
            db.session.add(new_item)
            db.session.flush()

            # 3. Handle Collection
            collection_name = form.collection.data
            if collection_name:
                collection = Collection.query.filter_by(name=collection_name).first()
                if not collection:
                    # If collection doesn't exist, create a new one
                    collection = Collection(name=collection_name)
                    db.session.add(collection)
                    db.session.flush()  # Get the collection ID
                    flash(f'Đã tạo bộ sưu tập mới: "{collection_name}"', 'info')
                new_item.collections.append(collection)

            # 4. Handle Image Uploads
            if form.image.data:
                files = request.files.getlist(form.image.name)
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                        unique_filename = f"{timestamp}_{filename}"

                        # Ensure upload folder exists
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        file.save(file_path)

                        # Create and add image record
                        product_image = ProductImage(
                            product_id=new_item.id,
                            image_url=unique_filename
                        )
                        db.session.add(product_image)

            # 5. Commit all changes
            db.session.commit()
            flash('Thêm sản phẩm thành công!', 'success')
            return redirect(url_for('admin.manage_products'))

        except Exception as e:
            db.session.rollback()
            print(f"Detailed error: {str(e)}")  # Debug print
            import traceback
            print("Traceback:", traceback.format_exc())  # Print full traceback
            flash(f'Đã xảy ra lỗi khi thêm sản phẩm: {str(e)}', 'error')

    return render_template('admin/add_product.html',
                         form=form,
                         title="Thêm sản phẩm mới",
                         collection_names=collection_names)


@admin_bp.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_item(product_id):
    item = Product.query.get_or_404(product_id)
    form = ShopItemForm(obj=item)

    # Get existing images
    existing_images = ProductImage.query.filter_by(product_id=item.id).all()

    # Get all collections for the datalist
    collections = Collection.query.all()
    collection_names = [c.name for c in collections]

    if form.validate_on_submit():
        try:
            # Update basic fields
            item.name = form.name.data
            item.description = form.description.data
            item.price = form.price.data
            item.stock = form.stock.data
            item.is_active = form.is_active.data
            item.is_featured = form.is_featured.data
            item.date_released = form.date_released.data

            # Handle collection
            collection_name = form.collection.data
            if collection_name:
                collection = Collection.query.filter_by(name=collection_name).first()
                if not collection:
                    collection = Collection(name=collection_name)
                    db.session.add(collection)
                    db.session.flush()
                    flash(f'Đã tạo bộ sưu tập mới: "{collection_name}"', 'info')
                item.collections = [collection]

            # Handle new image uploads
            if form.image.data and any(file.filename for file in form.image.data):
                files = request.files.getlist(form.image.name)
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                        unique_filename = f"{timestamp}_{filename}"

                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        file.save(file_path)

                        product_image = ProductImage(
                            product_id=item.id,
                            image_url=unique_filename
                        )
                        db.session.add(product_image)

            db.session.commit()
            flash('Cập nhật sản phẩm thành công!', 'success')
            return redirect(url_for('admin.manage_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật sản phẩm: {str(e)}', 'error')
            print(f"Error details: {str(e)}")

    # For GET requests, pre-fill collection if exists
    if item.collections:
        form.collection.data = item.collections[0].name

    return render_template('admin/edit_product.html',
                         form=form,
                         item=item,
                         existing_images=existing_images,
                         collection_names=collection_names)


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

@admin_bp.route('/products/delete-image/<int:image_id>', methods=['POST'])
@login_required
def delete_product_image(image_id):
    try:
        image = ProductImage.query.get_or_404(image_id)

        # Delete the physical file
        file_path = os.path.join(UPLOAD_FOLDER, image.image_url)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete the database record
        db.session.delete(image)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
