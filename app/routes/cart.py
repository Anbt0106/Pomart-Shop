from flask import Blueprint, request, redirect, url_for, flash, session, render_template, jsonify
from flask_login import login_required, current_user
from ..models.product import Product
from ..models.order import Order, OrderItem, Cart, PaymentTransaction, Discount
from ..models.user import User, UserAddress
from ..routes.form import CheckoutForm, PaymentForm
from .. import db
from datetime import datetime
import uuid

cart = Blueprint('cart', __name__)

@cart.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))

    if quantity <= 0:
        flash('Quantity must be positive', 'error')
        return redirect(url_for('views.product_detail', product_id=product_id))

    if quantity > product.stock:
        flash('Not enough stock available', 'error')
        return redirect(url_for('views.product_detail', product_id=product_id))

    # Initialize cart in session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    # Add or update product in cart
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += quantity
    else:
        cart[str(product_id)] = {
            'quantity': quantity,
            'price': float(product.price)
        }

    session['cart'] = cart
    flash('Product added to cart successfully!', 'success')
    return redirect(url_for('views.product_detail', product_id=product_id))

@cart.route('/cart')
def view_cart():
    """View cart contents"""
    cart_items = []
    total = 0
    
    if 'cart' in session and session['cart']:
        for product_id, item in session['cart'].items():
            product = Product.query.get(int(product_id))
            if product:
                subtotal = item['price'] * item['quantity']
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'subtotal': subtotal
                })
    
    # Get related products (random products for now)
    related_products = Product.query.filter(Product.stock > 0).order_by(db.func.random()).limit(4).all()
    
    return render_template('cart.html', cart_items=cart_items, total=total, related_products=related_products)

@cart.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update quantity in cart"""
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' in session and str(product_id) in session['cart']:
        if quantity <= 0:
            del session['cart'][str(product_id)]
        else:
            session['cart'][str(product_id)]['quantity'] = quantity
        session.modified = True
        
    return redirect(url_for('cart.view_cart'))

@cart.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
        flash('Item removed from cart', 'success')
    
    return redirect(url_for('cart.view_cart'))

@cart.route('/clear-cart')
def clear_cart():
    """Clear entire cart"""
    if 'cart' in session:
        session.pop('cart')
        flash('Cart cleared', 'success')
    
    return redirect(url_for('cart.view_cart'))

@cart.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart.view_cart'))
    
    # Get user's existing addresses
    user_addresses = UserAddress.query.filter_by(user_id=current_user.id).all()
    
    form = CheckoutForm()
    
    # Update address choices
    address_choices = [('new', 'Tạo địa chỉ mới')]
    for addr in user_addresses:
        address_choices.append((str(addr.id), f"{addr.recipient_name} - {addr.address[:50]}..."))
    form.address_choice.choices = address_choices
    
    # Calculate cart total
    cart_items = []
    subtotal = 0
    
    for product_id, item in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = item['price'] * item['quantity']
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': item['price'],
                'subtotal': item_total
            })
    
    # Apply discount if provided
    discount_amount = 0
    discount = None
    if form.discount_code.data:
        discount = Discount.query.filter_by(code=form.discount_code.data).first()
        if discount and discount.is_valid(subtotal):
            discount_amount = discount.calculate_discount(subtotal)
    
    total = subtotal - discount_amount
    shipping_fee = 30000 if total < 500000 else 0  # Free shipping for orders > 500k
    final_total = total + shipping_fee
    
    if form.validate_on_submit():
        try:
            # Handle address choice
            if form.address_choice.data == 'new':
                # Validate required fields for new address
                if not form.recipient_name.data or not form.phone_number.data or not form.address.data or not form.city.data or not form.country.data:
                    flash('Vui lòng điền đầy đủ thông tin địa chỉ mới', 'error')
                    return redirect(url_for('cart.checkout'))
                
                # Create new shipping address
                address = UserAddress(
                    user_id=current_user.id,
                    recipient_name=form.recipient_name.data,
                    phone_number=form.phone_number.data,
                    address=form.address.data,
                    city=form.city.data,
                    postal_code=form.postal_code.data,
                    country=form.country.data,
                    is_default=True
                )
                db.session.add(address)
                db.session.flush()  # Get the address ID
            else:
                # Use existing address
                address_id = int(form.address_choice.data)
                address = UserAddress.query.filter_by(id=address_id, user_id=current_user.id).first()
                if not address:
                    flash('Địa chỉ không hợp lệ', 'error')
                    return redirect(url_for('cart.checkout'))
            
            # Create order
            order = Order(
                user_id=current_user.id,
                address_id=address.id,
                total_amount=final_total,
                status='pending',
                payment_status='unpaid',
                discount_id=discount.id if discount else None
            )
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Create order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    quantity=item['quantity'],
                    price=item['price']
                )
                db.session.add(order_item)
                
                # Update product stock
                item['product'].stock -= item['quantity']
            
            # Create payment transaction
            payment = PaymentTransaction(
                order_id=order.id,
                user_id=current_user.id,
                amount=final_total,
                payment_method=form.payment_method.data,
                status='pending'
            )
            db.session.add(payment)
            
            # Commit all changes
            db.session.commit()
            
            # Clear cart
            session.pop('cart')
            
            flash('Order placed successfully! Order ID: ' + str(order.id), 'success')
            return redirect(url_for('cart.order_confirmation', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error placing order. Please try again.', 'error')
            print(f"Error: {e}")
    
    return render_template('checkout.html', 
                         form=form, 
                         cart_items=cart_items, 
                         user_addresses=user_addresses,
                         subtotal=subtotal,
                         discount_amount=discount_amount,
                         shipping_fee=shipping_fee,
                         total=total,
                         final_total=final_total)

@cart.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_confirmation.html', order=order)

@cart.route('/my-orders')
@login_required
def my_orders():
    """User's order history"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.placed_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@cart.route('/addresses')
@login_required
def manage_addresses():
    """Manage user's shipping addresses"""
    addresses = UserAddress.query.filter_by(user_id=current_user.id).order_by(UserAddress.is_default.desc()).all()
    return render_template('addresses.html', addresses=addresses)

@cart.route('/add-address', methods=['GET', 'POST'])
@login_required
def add_address():
    """Add new shipping address"""
    if request.method == 'POST':
        recipient_name = request.form.get('recipient_name')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        city = request.form.get('city')
        postal_code = request.form.get('postal_code')
        country = request.form.get('country')
        is_default = request.form.get('is_default') == 'on'
        
        if is_default:
            # Remove default from other addresses
            UserAddress.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        new_address = UserAddress(
            user_id=current_user.id,
            recipient_name=recipient_name,
            phone_number=phone_number,
            address=address,
            city=city,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        
        db.session.add(new_address)
        db.session.commit()
        
        flash('Địa chỉ đã được thêm thành công!', 'success')
        return redirect(url_for('cart.manage_addresses'))
    
    return render_template('add_address.html')

@cart.route('/edit-address/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    """Edit existing shipping address"""
    address = UserAddress.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        address.recipient_name = request.form.get('recipient_name')
        address.phone_number = request.form.get('phone_number')
        address.address = request.form.get('address')
        address.city = request.form.get('city')
        address.postal_code = request.form.get('postal_code')
        address.country = request.form.get('country')
        is_default = request.form.get('is_default') == 'on'
        
        if is_default and not address.is_default:
            # Remove default from other addresses
            UserAddress.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        address.is_default = is_default
        db.session.commit()
        
        flash('Địa chỉ đã được cập nhật thành công!', 'success')
        return redirect(url_for('cart.manage_addresses'))
    
    return render_template('edit_address.html', address=address)

@cart.route('/delete-address/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    """Delete shipping address"""
    address = UserAddress.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    if address.is_default:
        flash('Không thể xóa địa chỉ mặc định!', 'error')
        return redirect(url_for('cart.manage_addresses'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('Địa chỉ đã được xóa thành công!', 'success')
    return redirect(url_for('cart.manage_addresses'))

@cart.route('/set-default-address/<int:address_id>', methods=['POST'])
@login_required
def set_default_address(address_id):
    """Set address as default"""
    address = UserAddress.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    if not address.is_default:
        # Remove default from other addresses
        UserAddress.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        # Set this address as default
        address.is_default = True
        db.session.commit()
        
        flash('Đã đặt làm địa chỉ mặc định!', 'success')

    return redirect(url_for('cart.manage_addresses'))

@cart.route('/order-detail/<int:order_id>')
@login_required
def order_detail(order_id):
    """View detailed information of a specific order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_detail.html', order=order)

@cart.route('/cancel-order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order (only if pending and unpaid)"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

    if order.status != 'pending' or order.payment_status != 'unpaid':
        flash('Không thể hủy đơn hàng này!', 'error')
        return redirect(url_for('cart.my_orders'))

    try:
        # Restore product stock
        for item in order.items:
            item.product.stock += item.quantity

        # Update order status
        order.status = 'canceled'

        # Update payment transaction status
        for transaction in order.payment_transactions:
            transaction.status = 'canceled'

        db.session.commit()
        flash('Đơn hàng đã được hủy thành công!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi hủy đơn hàng!', 'error')
        print(f"Error canceling order: {e}")

    return redirect(url_for('cart.my_orders'))

@cart.route('/reorder/<int:order_id>')
@login_required
def reorder(order_id):
    """Add items from a previous order to cart"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    items_added = 0

    for item in order.items:
        # Check if product is still available
        if item.product.is_active and item.product.stock > 0:
            product_id_str = str(item.product.id)
            quantity_to_add = min(item.quantity, item.product.stock)

            if product_id_str in cart:
                # Check if we can add more
                current_quantity = cart[product_id_str]['quantity']
                max_addable = item.product.stock - current_quantity
                if max_addable > 0:
                    cart[product_id_str]['quantity'] += min(quantity_to_add, max_addable)
                    items_added += 1
            else:
                cart[product_id_str] = {
                    'quantity': quantity_to_add,
                    'price': float(item.product.price)
                }
                items_added += 1

    session['cart'] = cart
    session.modified = True

    if items_added > 0:
        flash(f'Đã thêm {items_added} sản phẩm vào giỏ hàng!', 'success')
    else:
        flash('Không có sản phẩm nào có thể thêm vào giỏ hàng!', 'warning')

    return redirect(url_for('cart.view_cart'))

@cart.route('/apply-discount', methods=['POST'])
@login_required
def apply_discount():
    """Apply discount code during checkout"""
    discount_code = request.form.get('discount_code', '').strip()

    if not discount_code:
        flash('Vui lòng nhập mã giảm giá!', 'error')
        return redirect(url_for('cart.checkout'))

    # Calculate current cart total
    cart_total = 0
    if 'cart' in session and session['cart']:
        for product_id, item in session['cart'].items():
            cart_total += item['price'] * item['quantity']

    discount = Discount.query.filter_by(code=discount_code).first()
    
    if not discount:
        flash('Mã giảm giá không tồn tại!', 'error')
    elif not discount.is_valid(cart_total):
        flash('Mã giảm giá không hợp lệ hoặc đã hết hạn!', 'error')
    else:
        # Store discount code in session for checkout
        session['discount_code'] = discount_code
        discount_amount = discount.calculate_discount(cart_total)
        flash(f'Áp dụng mã giảm giá thành công! Giảm {"{:,.0f}".format(discount_amount)} VND', 'success')

    return redirect(url_for('cart.checkout'))

@cart.route('/remove-discount', methods=['POST'])
@login_required
def remove_discount():
    """Remove applied discount code"""
    if 'discount_code' in session:
        session.pop('discount_code')
        flash('Đã xóa mã giảm giá!', 'info')

    return redirect(url_for('cart.checkout'))
