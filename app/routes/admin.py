# app/routes/admin.py
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime
from sqlalchemy import func

from app import db
from app.models import Product, User, Order, Collection, ProductImage
from app.routes.form import ShopItemForm


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
        if form.validate():
            try:
                print("Form validated successfully")  # Debug print
                # 1. Create Product instance
                new_item = Product(
                    name=form.name.data,
                    description=form.description.data,
                    price=form.price.data,
                    stock=form.stock.data,
                    is_active=form.is_active.data or False,
                    is_featured=form.is_featured.data or False,
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
                    if not hasattr(new_item, 'collections') or new_item.collections is None:
                        new_item.collections = []
                    new_item.collections.append(collection)
                else:
                    # Initialize empty collections list if no collection name provided
                    if not hasattr(new_item, 'collections') or new_item.collections is None:
                        new_item.collections = []

                # 4. Handle Image Uploads
                if form.image.data:
                    for file in form.image.data:
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
        else:
            # Form validation failed
            print("Form validation errors:", form.errors)  # Debug print
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Lỗi ở trường {field}: {error}', 'error')

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
            item.is_active = form.is_active.data or False
            item.is_featured = form.is_featured.data or False
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
                if not hasattr(item, 'collections') or item.collections is None:
                    item.collections = []
                item.collections = [collection]
            else:
                # Clear collections if no collection name provided
                if hasattr(item, 'collections'):
                    item.collections.clear()

            # Handle new image uploads
            if form.image.data:
                for file in form.image.data:
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
    if hasattr(item, 'collections') and item.collections and len(item.collections) > 0:
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

# User Management Routes
@admin_bp.route('/users')
@login_required
def users_list():
    """Display list of all users"""
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('views.home'))

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)

    # Build query
    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )

    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    elif status_filter == 'admin':
        query = query.filter(User.is_admin == True)

    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('admin/users_list.html', users=users, search=search, status_filter=status_filter)

# Order Management Routes
@admin_bp.route('/orders')
@login_required
def orders_list():
    """Display list of all orders"""
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('views.home'))

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    payment_filter = request.args.get('payment', '', type=str)

    # Build query with joins to get user information
    query = Order.query.join(User)

    if search:
        query = query.filter(
            db.or_(
                Order.id.like(f'%{search}%'),
                User.username.contains(search),
                User.email.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )

    if status_filter:
        query = query.filter(Order.status == status_filter)

    if payment_filter:
        query = query.filter(Order.payment_status == payment_filter)

    orders = query.order_by(Order.placed_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('admin/orders_list.html',
                         orders=orders,
                         search=search,
                         status_filter=status_filter,
                         payment_filter=payment_filter)

@admin_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Display order details"""
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('views.home'))

    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/update-shipping', methods=['POST'])
@login_required
def update_shipping_info(order_id):
    """Update shipping information for an order"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()

        # Update shipping fields
        if 'tracking_number' in data:
            order.tracking_number = data['tracking_number']

        if 'estimated_delivery' in data:
            # Parse datetime string to datetime object
            estimated_delivery_str = data['estimated_delivery']
            if estimated_delivery_str:
                order.estimated_delivery = datetime.strptime(estimated_delivery_str, '%Y-%m-%dT%H:%M')

        if 'shipping_method' in data:
            order.shipping_method = data['shipping_method']

        if 'shipping_fee' in data:
            order.shipping_fee = float(data['shipping_fee'])

        if 'shipping_notes' in data:
            order.shipping_notes = data['shipping_notes']

        # Auto-update shipped_at when tracking number is added
        if 'tracking_number' in data and data['tracking_number'] and not order.shipped_at:
            order.shipped_at = datetime.utcnow()
            if order.status == 'pending':
                order.status = 'shipped'

        # Auto-update delivered_at when status changes to delivered
        if order.status == 'delivered' and not order.delivered_at:
            order.delivered_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Cập nhật thông tin vận chuyển thành công!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 400


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()

        new_status = data.get('status')
        if new_status not in ['pending', 'shipped', 'delivered', 'canceled']:
            return jsonify({
                'success': False,
                'message': 'Trạng thái không hợp lệ'
            }), 400

        old_status = order.status
        order.status = new_status

        # Auto-update timestamps based on status
        if new_status == 'shipped' and not order.shipped_at:
            order.shipped_at = datetime.utcnow()
        elif new_status == 'delivered' and not order.delivered_at:
            order.delivered_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Cập nhật trạng thái từ "{order.status_display}" thành công!',
            'new_status': new_status,
            'new_status_display': order.status_display
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 400


@admin_bp.route('/orders/<int:order_id>/update-payment', methods=['POST'])
@login_required
def update_payment_status(order_id):
    """Update payment status"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()

        new_payment_status = data.get('payment_status')
        if new_payment_status not in ['unpaid', 'paid', 'refunded']:
            return jsonify({
                'success': False,
                'message': 'Trạng thái thanh toán không hợp lệ'
            }), 400

        order.payment_status = new_payment_status

        # Auto-update paid_at when status changes to paid
        if new_payment_status == 'paid' and not order.paid_at:
            order.paid_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Cập nhật trạng thái thanh toán thành công!',
            'new_payment_status': new_payment_status,
            'new_payment_status_display': order.payment_status_display
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 400

@admin_bp.route('/orders/statistics')
@login_required
def order_statistics():
    """Display order statistics"""
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('views.home'))

    # Get order statistics
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    shipped_orders = Order.query.filter_by(status='shipped').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    canceled_orders = Order.query.filter_by(status='canceled').count()

    # Get payment statistics
    paid_orders = Order.query.filter_by(payment_status='paid').count()
    unpaid_orders = Order.query.filter_by(payment_status='unpaid').count()
    refunded_orders = Order.query.filter_by(payment_status='refunded').count()

    # Get revenue statistics
    total_revenue = db.session.query(func.sum(Order.total_amount)).filter_by(payment_status='paid').scalar() or 0
    pending_revenue = db.session.query(func.sum(Order.total_amount)).filter_by(payment_status='unpaid').scalar() or 0

    statistics = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'canceled_orders': canceled_orders,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'refunded_orders': refunded_orders,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue
    }

    return render_template('admin/order_statistics.html', statistics=statistics)
